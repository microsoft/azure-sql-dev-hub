# Prompt end-to-end evaluation

This harness sends Azure SQL Developer Hub build prompts to GitHub Copilot CLI
and validates the resulting applications against Azure SQL Database.

## Set up

Run the evaluation commands from this directory:

```bash
cd eval
```

Create and activate a virtual environment, then install the pinned dependencies:

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install and sign in to:

1. [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
2. [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
3. Node.js 20 or newer and npm
4. Python 3.10 or newer
5. .NET SDK 8 or newer
6. [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
7. [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)

On macOS:

```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
npm install -g azurite
```

## Configure Azure

Create the local configuration file:

```bash
cp validation.EXAMPLE.env validation.env
```

`validation.env` is ignored by Git and supports these settings:

| Setting | Description |
|---|---|
| `HUB_EVAL_AZURE_TENANT_ID` | Microsoft Entra tenant ID for the authenticated Azure CLI account. |
| `HUB_EVAL_AZURE_SUBSCRIPTION_ID` | Azure subscription used by the evaluation. |
| `HUB_EVAL_AZURE_LOCATION` | Region for Azure SQL resources. |
| `HUB_EVAL_EXISTING_RESOURCE_GROUP` | Existing resource group to use, or blank for a harness-provisioned group. |
| `HUB_EVAL_EXISTING_SQL_SERVER` | Existing Azure SQL logical server to use, or blank for a harness-provisioned server. |
| `HUB_EVAL_EMBEDDING_LOCATION` | Region for an Azure OpenAI resource. |
| `HUB_EVAL_EMBEDDING_ENDPOINT` | Existing Azure OpenAI endpoint, or blank for harness provisioning. |
| `HUB_EVAL_EMBEDDING_DEPLOYMENT` | Existing embedding deployment name. |
| `HUB_EVAL_EMBEDDING_DIMENSION` | Existing embedding deployment output dimension. |

Set both existing SQL values or leave both blank. Set all three existing
embedding values or leave all three blank.

Verify the Azure CLI context:

```bash
az cloud show --query name --output tsv
az account show \
  --query '{tenant:tenantId,subscription:id,state:state}' \
  --output table
```

### Required resource providers

- `Microsoft.Sql`
- `Microsoft.CognitiveServices` when `rag-app` requires a harness-provisioned
  Azure OpenAI resource

Register providers when needed:

```bash
az provider register --namespace Microsoft.Sql --wait
az provider register --namespace Microsoft.CognitiveServices --wait
```

### Required permissions

#### Harness-provisioned resource group and SQL server

- **Contributor** at subscription scope.
- For a harness-provisioned Azure OpenAI resource: **Role Based Access Control
  Administrator** at subscription scope.
- For an existing Azure OpenAI deployment: **Cognitive Services OpenAI User**
  on that Azure OpenAI account.

#### Existing resource group and SQL server

- **SQL Server Contributor** at resource-group scope.
- A Microsoft Entra server login and mapped user in virtual `master`, with the
  login assigned to `##MS_DatabaseManager##`.
- An existing server firewall rule that permits the client IP.
- For a harness-provisioned Azure OpenAI resource: **Cognitive Services
  Contributor** at subscription scope and **Role Based Access Control
  Administrator** at resource-group scope.
- For an existing Azure OpenAI deployment: **Cognitive Services OpenAI User**
  on that Azure OpenAI account.

## Verify Copilot CLI

```bash
copilot --version
copilot -p "Reply with exactly AUTHENTICATED." \
  --model gpt-5.4 \
  --silent \
  --stream off \
  --disable-builtin-mcps \
  --allow-all-tools
```

Use `copilot login` if authentication is required.

## Commands

### Preview a run

Shows the selected models and scenarios without running them:

```bash
python run_evals.py --dry-run
```

### Run preflight

Checks the Azure configuration and permissions required by the selected
scenarios:

```bash
python run_evals.py \
  --scenario rag-app \
  --preflight
```

The result is written to `runs/<run-id>/preflight.json`.

### Run all scenarios with one model

```bash
python run_evals.py --model gpt-5.4
```

```bash
python run_evals.py --model claude-sonnet-5
```

### Run all scenarios with both models

```bash
python run_evals.py \
  --model gpt-5.4 \
  --model claude-sonnet-5
```

### Run selected scenarios

Repeat `--scenario` to select more than one:

```bash
python run_evals.py \
  --model gpt-5.4 \
  --scenario javascript-app \
  --scenario rag-app
```

Available scenarios:

- `javascript-app`
- `python-api`
- `rag-app`
- `serverless-api`
- `event-driven-app`
- `multi-tenant`

Scenario dependencies are included automatically. `multi-tenant` includes
`javascript-app`; `event-driven-app` includes `serverless-api`.

### Run with longer timeouts

```bash
python run_evals.py \
  --agent-timeout-seconds 3600 \
  --validation-timeout-seconds 1200
```

### Retain generated workspaces

```bash
python run_evals.py --keep-workspaces
```

## Scenario coverage

| Scenario | Validated result |
|---|---|
| `javascript-app` | A Next.js application returns rows from an Azure SQL table. |
| `python-api` | A Python API lists, creates, and completes task rows. |
| `rag-app` | Azure SQL stores native vectors and returns ranked similarity results. |
| `serverless-api` | An Azure Function returns rows through an Azure SQL binding. |
| `event-driven-app` | A database insert triggers the expected function invocation. |
| `multi-tenant` | Row-level security isolates data between tenants. |

## Run artifacts

Runs are written under `runs/<UTC timestamp>-<unique suffix>/`:

```text
runs/<run-id>/
├── manifest.json                         // Selected models, scenarios, and limits
├── preflight.json                        // Azure context and permission results
├── results.json                          // Complete run result rollup
├── summary.md                            // Human-readable result summary
└── <model>/
    ├── azure/                            // Azure command metadata, stdout, and stderr
    ├── resources.json                    // Azure resource names and identifiers
    ├── results.json                      // Result rollup for this model
    ├── scenarios/
    │   └── <scenario>/
    │       ├── prompt.md                 // Exact prompt sent to the agent
    │       ├── result.json               // Result for this scenario and model
    │       ├── agent/
    │       │   ├── *.json                // Copilot command metadata
    │       │   ├── *.stdout.txt          // Copilot JSONL event stream
    │       │   ├── *.stderr.txt          // Copilot stderr
    │       │   └── copilot-logs/         // Copilot session logs
    │       └── validation/
    │           ├── *.json                // Validator command metadata
    │           ├── *.stdout.txt          // Validator output and server logs
    │           └── *.stderr.txt          // Validator stderr
    └── workspaces/                       // Present when --keep-workspaces is used
        └── <scenario>/                   // Agent-generated application
```

## Run the harness tests

The harness tests do not invoke Copilot CLI or create Azure resources:

```bash
python -m unittest discover -s tests -v
```
