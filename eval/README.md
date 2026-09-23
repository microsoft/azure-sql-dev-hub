# Prompt end-to-end evaluation

This harness gives each build prompt to GitHub Copilot CLI, lets the agent create
the example in an isolated local workspace, and independently checks the result.
It creates a disposable Azure resource group for each model and deletes that
resource group at the end, including when a prompt, validator, or agent fails. A
configured existing-server mode instead creates and deletes only uniquely named
evaluation resources.

The harness uses `mssql-python` and `azure-identity` for independent SQL
assertions. Create an isolated environment and install the pinned dependencies:

```bash
python3 -m venv eval/.venv
eval/.venv/bin/python -m pip install -r eval/requirements.txt
```

## Before you run it

Install and sign in to:

1. [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
2. [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
3. Node.js 20 or newer and npm
4. Python 3.10 or newer
5. .NET SDK 8 or newer
6. [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
7. [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)

On macOS, the missing Functions tools can be installed with:

```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
npm install -g azurite
```

Create the local configuration file:

```bash
cp eval/validation.EXAMPLE.env eval/validation.env
```

Edit `eval/validation.env` with the tenant, subscription, regions, and optional
existing SQL server or embedding deployment. The file is ignored by Git. The
harness always selects the public `AzureCloud`; every account-specific Azure
default is loaded from this file. Command-line options only override its values
for a single run.

Verify the authenticated account before running:

```bash
az cloud show --query name --output tsv
az account show --query '{tenant:tenantId,subscription:id,state:state}' --output table
```

When both existing-resource properties are blank, the harness creates and
deletes an entire resource group. When both are set, it creates uniquely named
database, firewall, and optional embedding resources, then deletes each created
resource individually. It never deletes the configured existing server or
resource group.

Copilot CLI noninteractive mode requires an authenticated Copilot session. The
harness disables the built-in GitHub MCP server and grants unattended local tool
execution inside each generated workspace.

Check that Copilot CLI is installed:

```bash
command -v copilot
copilot --version
```

Both commands should print a path/version. If `command -v` prints nothing,
install Copilot CLI using the linked GitHub instructions above.

Check authentication with a minimal noninteractive request:

```bash
copilot -p "Reply with exactly AUTHENTICATED." \
  --model gpt-5.4 \
  --silent \
  --stream off \
  --disable-builtin-mcps \
  --allow-all-tools
```

The command should print `AUTHENTICATED` and exit zero. If it reports an
authentication error or opens an authentication flow, run:

```bash
copilot login
```

## Check the plan without creating anything

From the repository root:

```bash
eval/.venv/bin/python eval/run_evals.py --dry-run
```

## Run with a GPT model

```bash
eval/.venv/bin/python eval/run_evals.py --model gpt-5.4
```

## Run with a Claude model through Copilot CLI

```bash
eval/.venv/bin/python eval/run_evals.py --model claude-sonnet-5
```

Both model identifiers were verified with GitHub Copilot CLI 1.0.85. To run the
same scenario matrix with both:

```bash
eval/.venv/bin/python eval/run_evals.py \
  --model gpt-5.4 \
  --model claude-sonnet-5
```

The default agent timeout is 45 minutes per prompt. Independent validation gets
15 minutes. Override them when needed:

```bash
eval/.venv/bin/python eval/run_evals.py \
  --agent-timeout-seconds 3600 \
  --validation-timeout-seconds 1200
```

## Run selected scenarios

Repeat `--scenario` to select more than one:

```bash
eval/.venv/bin/python eval/run_evals.py \
  --model gpt-5.4 \
  --scenario javascript-app \
  --scenario multi-tenant
```

Dependencies are automatic. Selecting `multi-tenant` also runs
`javascript-app`; selecting `event-driven-app` also runs `serverless-api`.

Available scenarios:

- `javascript-app`
- `python-api`
- `rag-app`
- `serverless-api`
- `event-driven-app`
- `multi-tenant`

## RAG embedding deployment

When `rag-app` is selected, the harness first tries to create an Azure OpenAI Service
account and a `text-embedding-3-small` deployment in the disposable resource
group. It uses Microsoft Entra authentication and does not retrieve or record an
API key.

Model availability and quota vary by subscription. If automatic provisioning is
unavailable, the RAG scenario uses the prompt's deterministic fixture-vector
fallback. That path validates SQL `VECTOR` storage and `VECTOR_DISTANCE`
mechanics but does not claim semantic retrieval quality. An existing deployment
can be supplied without putting a key on the command line:

```bash
eval/.venv/bin/python eval/run_evals.py \
  --model gpt-5.4 \
  --embedding-endpoint https://example.openai.azure.com/ \
  --embedding-deployment text-embedding-3-small \
  --embedding-dimension 1536
```

To deliberately use the fixture-vector path without attempting provisioning:

```bash
eval/.venv/bin/python eval/run_evals.py --skip-embedding-provision
```

## Cleanup behavior

By default, each model gets a uniquely named resource group with the prefix
`rg-sqlhub-eval-`. The runner:

1. Creates the group before any prompt runs.
2. Executes all requested scenarios inside that group.
3. Calls blocking `az group delete` in a `finally` block.
4. Retries deletion up to three times.
5. Verifies `az group exists` returns `false`.

Do not use `kill -9` or power off the machine during a run. No process can
guarantee cleanup after an uncatchable termination. If a machine or process is
forcibly terminated, use the exact group name from `resources.json`:

```bash
eval/.venv/bin/python eval/run_evals.py --cleanup-only rg-sqlhub-eval-0123456789
```

The cleanup command refuses resource groups outside the evaluation prefix.

## Results

The terminal prints timestamped, flushed lifecycle events while the detailed
stdout and stderr continue to be written to evidence files. Output includes:

- START and END for the complete run, each model, and each prompt scenario
- elapsed duration and PASS/FAIL status for every END event
- Azure resource create/delete commands
- Copilot CLI, build, test, and validation commands
- local API, Function, and Azurite process start/stop events
- independent SQL probes
- safely redacted error summaries and exact evidence paths

After cleanup, the final console block prints the result for each
scenario/harness/model combo:

```text
✅ PASS | scenario=javascript-app | harness=copilot | model=gpt-5.4
⚠️ BLOCKED | scenario=multi-tenant | harness=copilot | model=gpt-5.4 | details=dependencies did not pass: javascript-app
❌ FAIL | scenario=python-api | harness=copilot | model=claude-sonnet-5 | details=validation failed: ...
```

Runs are written under `eval/runs/<UTC timestamp>-<unique suffix>/`. Each run contains:

- `manifest.json`: exact models, scenarios, timeouts, and source limitation
- `resources.json`: disposable resource names, never credentials
- `prompt.md`: the complete prompt sent to the agent
- Copilot JSONL, stderr, and local Copilot logs
- Validator command output and server logs
- `results.json` and `summary.md`

Generated workspaces are removed after the run by default. Add
`--keep-workspaces` when debugging an implementation failure. Azure resources are
still deleted.

## Prompt-specific verification files

Each prompt has one verification file with the exact same filename stem:

| Prompt | Verification |
|---|---|
| `build/javascript-app.md` | `eval/verifications/javascript-app.py` |
| `build/python-api.md` | `eval/verifications/python-api.py` |
| `build/rag-app.md` | `eval/verifications/rag-app.py` |
| `build/serverless-api.md` | `eval/verifications/serverless-api.py` |
| `build/event-driven-app.md` | `eval/verifications/event-driven-app.py` |
| `build/multi-tenant.md` | `eval/verifications/multi-tenant.py` |

`hub_eval/scenarios.py` loads these modules and refuses a filename/prompt-stem
mismatch.

## Local harness tests

These tests do not create Azure resources or invoke a real agent:

```bash
PYTHONPATH=eval eval/.venv/bin/python -m unittest discover -s eval/tests -v
```

## Adding Codex CLI or Claude Code

Agent invocation is isolated behind the `AgentCli` protocol in
`hub_eval/agents.py`. To add another CLI:

1. Implement `name` and `run(AgentRequest)`.
2. Use `CommandRunner` so timeouts and process-group cleanup remain consistent.
3. Produce immutable stdout, stderr, and command metadata in the supplied
   evidence directory.
4. Register the adapter in `create_agent`.
5. Run it with `--agent <registered-name>` after the adapter has unit coverage.

The Azure lifecycle and all end-state validators are provider-independent.

## Validation source limitation

`Hub-Prompt-Validation.docx` was supplied as a DRM-protected Office document. The
headless environment could identify `DRMEncryptedDataSpace` but could not decrypt
its text. The criteria were subsequently supplied as a table and are implemented
as follows:

| Scenario | Required end state |
|---|---|
| JavaScript app | Next.js app starts and one HTTP request returns rows from the agent-created table. |
| Python API | `GET /tasks` returns 200 with JSON rows and `POST /tasks` creates one row. |
| RAG | A native `VECTOR` column exists and one `VECTOR_DISTANCE` query returns ranked rows. |
| Serverless API | The Function runs locally and one HTTP GET returns rows through the SQL binding. |
| Event-driven app | Change Tracking is enabled and one insert triggers the function exactly once. |
| Multi-tenant app | The RLS policy exists and the isolation test proves tenant A cannot read tenant B rows. |

The validators also retain compatible checks from each published prompt's
`Validation rules` section.
