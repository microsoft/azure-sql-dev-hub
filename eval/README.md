# Prompt end-to-end evaluation

This harness sends Azure SQL Developer Hub build prompts to GitHub Copilot CLI,
Claude Code, or Codex CLI and validates the resulting applications against
Azure SQL Database.

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
3. [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup)
4. [Codex CLI](https://developers.openai.com/codex/cli)
5. Node.js 20 or newer and npm
6. Python 3.10 or newer
7. .NET SDK 8 or newer
8. [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
9. [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)

The harness uses each agent CLI's existing authentication and does not sign in
on your behalf.

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

## Configure a run

Copy the example configuration:

```bash
cp configuration.EXAMPLE.yml configuration.yml
```

`configuration.yml` is ignored by Git. It defines the ordered harnesses,
models, scenarios, timeouts, and workspace retention setting for a run.
`validation.env` remains separate and contains the Azure settings.

Use either `--configuration` or repeatable `--target HARNESS:MODEL` options,
not both. Any `--scenario` options replace the scenarios in the YAML file.

## Commands

### Preview a run

Shows the selected targets and scenarios without running them:

```bash
python run_evals.py --configuration configuration.yml --dry-run
```

### Run from the configuration file

```bash
python run_evals.py --configuration configuration.yml
```

### Run selected targets directly

```bash
python run_evals.py \
  --target copilot:gpt-5.4 \
  --target claude:claude-sonnet-5 \
  --target codex:gpt-6-sol
```

Without `--configuration` or `--target`, the default target is
`copilot:gpt-5.4`.

### List models

Lists the documented model options for a harness:

```bash
python run_evals.py --list-models copilot
python run_evals.py --list-models claude
python run_evals.py --list-models codex
```

Account policy may limit availability. Use agent preflight to verify access.

### Run preflight

Check agent installation, authentication, and model access:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight:agents
```

Check Azure configuration and permissions:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight:permissions
```

Run both checks:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight
```

The result is written to `runs/<run-id>/preflight.json`. Agent-only preflight
does not require `validation.env`.

### Run selected scenarios

Repeat `--scenario` to select more than one:

```bash
python run_evals.py \
  --configuration configuration.yml \
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
  --configuration configuration.yml \
  --agent-timeout-seconds 3600 \
  --validation-timeout-seconds 1200
```

### Retain generated workspaces

```bash
python run_evals.py \
  --configuration configuration.yml \
  --keep-workspaces
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
├── manifest.json
├── preflight.json
├── results.json
├── summary.md
└── <harness>/
    └── <model>/
        ├── azure/
        ├── resources.json
        ├── results.json
        ├── scenarios/
        │   └── <scenario>/
        │       ├── prompt.md
        │       ├── result.json
        │       ├── agent/
        │       └── validation/
        └── workspaces/                  # Present when --keep-workspaces is used
```

## Run the harness tests

The harness tests use fake agent executables and do not invoke real coding
agents or create Azure resources:

```bash
python -m unittest discover -s tests -v
```
