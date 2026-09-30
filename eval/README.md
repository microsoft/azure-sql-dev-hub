# Prompt end-to-end evaluation

This coding-agent-CLI-neutral harness sends Azure SQL Developer Hub build
prompts to Copilot CLI, Claude Code, or Codex CLI and independently validates
the resulting applications against Azure SQL Database.

## Set up

Run evaluation commands from this directory:

```bash
cd eval
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install Node.js 20+, Python 3.10+, .NET SDK 8+, Azure Functions Core Tools v4,
Azurite, and these authenticated CLIs:

1. [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
2. [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
3. [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup)
4. [Codex CLI](https://developers.openai.com/codex/cli)

The harness uses existing authenticated CLI state. It never copies that state
into run output and does not authenticate an agent for you.

### Verify Copilot CLI

```bash
copilot --version
copilot -p "Reply with exactly AUTHENTICATED." \
  --model gpt-5.4 --silent --stream off \
  --disable-builtin-mcps --allow-all-tools
```

Use `copilot login` if authentication is required.

### Verify Claude Code CLI

This harmless prompt does not ask Claude to edit files:

```bash
claude --version
claude -p "Reply with exactly AUTHENTICATED." \
  --model claude-sonnet-5 \
  --output-format stream-json --verbose \
  --permission-mode bypassPermissions --permission-prompts none \
  --safe-mode --strict-mcp-config --no-session-persistence --no-chrome
```

Sign in with the normal Claude Code authentication flow before evaluating.
Do not put Anthropic credentials in the evaluation env file.

### Verify Codex CLI

Install Codex using the official npm package, authenticate once, and inspect
authentication state with:

```bash
npm install -g @openai/codex
codex login
codex --version
codex login status
codex exec --json --ephemeral \
  --ignore-user-config --ignore-rules --skip-git-repo-check \
  --config 'approval_policy="never"' \
  --model gpt-6-sol --cd "$PWD" \
  --sandbox read-only \
  "Reply with exactly AUTHENTICATED. Do not use tools."
```

The generated-workspace execution template is:

```bash
codex exec --json --ephemeral \
  --ignore-user-config --ignore-rules --skip-git-repo-check \
  --config 'approval_policy="never"' \
  --config sandbox_workspace_write.network_access=true \
  --model MODEL --cd GENERATED_WORKSPACE \
  --sandbox workspace-write \
  "PROMPT"
```

## Configure Azure

```bash
cp validation.EXAMPLE.env validation.env
```

`validation.env` is ignored by Git. It contains only Azure account, resource,
and embedding settings:

| Setting | Description |
|---|---|
| `HUB_EVAL_AZURE_TENANT_ID` | Microsoft Entra tenant ID for Azure CLI. |
| `HUB_EVAL_AZURE_SUBSCRIPTION_ID` | Evaluation subscription. |
| `HUB_EVAL_AZURE_LOCATION` | Region for Azure SQL resources. |
| `HUB_EVAL_EXISTING_RESOURCE_GROUP` | Existing resource group, or blank to provision one. |
| `HUB_EVAL_EXISTING_SQL_SERVER` | Existing logical server, or blank to provision one. |
| `HUB_EVAL_EMBEDDING_LOCATION` | Region for an Azure OpenAI resource. |
| `HUB_EVAL_EMBEDDING_ENDPOINT` | Existing Azure OpenAI endpoint, or blank. |
| `HUB_EVAL_EMBEDDING_DEPLOYMENT` | Existing embedding deployment. |
| `HUB_EVAL_EMBEDDING_DIMENSION` | Existing embedding output dimension. |

Set both existing SQL values or neither. Set all three existing embedding
values or none. Required permissions and providers are unchanged: the
authenticated identity needs the documented Azure SQL and Azure OpenAI
permissions for existing or harness-provisioned resources.

## Evaluation configuration

Copy [`configuration.EXAMPLE.yml`](configuration.EXAMPLE.yml) to
`configuration.yml`. Exactly `eval/configuration.yml` is locally ignored while
`configuration.EXAMPLE.yml` remains tracked. The versioned YAML owns the
complete non-secret run plan; `validation.env` remains separate and Azure-only.

| Field | Rules |
|---|---|
| `schema_version` | Required integer; currently `1`. |
| `scenarios` | Ordered, non-empty list of known scenario names. |
| `agent_timeout_seconds` | Integer, at least 60. |
| `validation_timeout_seconds` | Integer, at least 30. |
| `keep_workspaces` | Boolean. |
| `harnesses` | Ordered, non-empty list of harness mappings. |
| `harnesses[].name` | Unique `copilot`, `claude`, or `codex`. |
| `harnesses[].models` | Ordered, non-empty, unique list of nonblank model strings. |

Harnesses expand in declaration order and each model expands in list order.
Unknown or missing properties, unknown scenarios/harnesses, duplicates, wrong
types, short timeouts, and normalized output-path collisions are rejected.
Arbitrary adapter arguments and secrets are not accepted.
Model strings are intentionally not restricted to the built-in catalogs because
providers evolve and full model IDs remain valid.

The tracked example expands this shape:

```yaml
harnesses:
  - name: copilot
    models: [gpt-5.4, claude-sonnet-5]
  - name: claude
    models: [claude-sonnet-5]
  - name: codex
    models: [gpt-6-sol]
```

When `--configuration` is used, one or more `--scenario` options replace the
entire YAML scenario list. Explicit `--agent-timeout-seconds`,
`--validation-timeout-seconds`, `--keep-workspaces`, or
`--no-keep-workspaces` override their YAML values. Omitted options retain YAML
values.

## Commands

Preview the default `copilot:gpt-5.4` run:

```bash
python run_evals.py --dry-run
```

Run the exact three-target ad hoc comparison:

```bash
python run_evals.py \
  --target copilot:gpt-5.4 \
  --target copilot:claude-sonnet-5 \
  --target claude:claude-sonnet-5
```

Add `--dry-run` to preview it without invoking either agent. Run from YAML:

```bash
python run_evals.py \
  --env-file validation.env \
  --configuration configuration.yml
```

Preview the example configuration:

```bash
python run_evals.py \
  --configuration configuration.EXAMPLE.yml \
  --dry-run
```

Run Claude directly:

```bash
python run_evals.py --target claude:claude-sonnet-5
```

Run Codex directly:

```bash
python run_evals.py --target codex:gpt-6-sol
```

Run two models through Copilot:

```bash
python run_evals.py \
  --target copilot:gpt-5.4 \
  --target copilot:claude-sonnet-5
```

Override YAML settings:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --scenario rag-app \
  --agent-timeout-seconds 3600 \
  --validation-timeout-seconds 1200 \
  --keep-workspaces
```

List the documented fallback catalog without `validation.env` or an installed
agent executable:

```bash
python run_evals.py --list-models copilot
python run_evals.py --list-models claude
python run_evals.py --list-models codex
```

The JSON output is generated from the single catalog used by harness
validation; use the command rather than copying a second model list into
documentation. It includes current CLI-style Copilot IDs and `auto`, Claude
aliases and current full IDs, and current Codex IDs. Account or organization
policy may reduce availability; `--preflight:agents` is authoritative for the
signed-in account.

Probe executable availability, authentication, and model access for every
resolved target without Azure configuration:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight:agents
```

Each agent probe sends a harmless exact-response prompt. Copilot disables
custom instructions and built-in MCPs and exposes no effective tools; Claude
uses safe mode, strict MCP configuration, `dontAsk`, and no tools; Codex uses
its isolated read-only sandbox with approval disabled and without the
workspace-write network override. Probes continue after failures, capture
command evidence, and can incur a small provider/model charge.

Run only the existing Azure context/provider/permission checks, without
constructing an agent:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight:permissions
```

Run both components into one run directory and report:

```bash
python run_evals.py \
  --configuration configuration.yml \
  --preflight
```

Agent-only preflight and model listing do not require `validation.env`.
Permissions-only preflight, combined preflight, cleanup, and live evaluation
still require it. Every preflight mode returns nonzero if any requested
component fails. `--preflight:agents`, `--preflight:permissions`,
`--preflight`, `--list-models`, `--dry-run`, and `--cleanup-only` are mutually
exclusive operation modes.

`--configuration` and repeatable `--target HARNESS:MODEL` are mutually
exclusive. The former `--agent` and `--model` options were intentionally
removed. Replace `--agent claude --model MODEL` with
`--target claude:MODEL`, and replace `--model MODEL` with
`--target copilot:MODEL`.

Available scenarios are `javascript-app`, `python-api`, `rag-app`,
`serverless-api`, `event-driven-app`, and `multi-tenant`. Dependencies are
included automatically.

## Run artifacts

Every target has its own Azure environment and evidence directory:

```text
runs/<run-id>/
├── manifest.json
├── configuration.yml                   # exact source, configuration runs only
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
        │       │   ├── *-<harness>.json
        │       │   ├── *-<harness>.stdout.txt
        │       │   ├── *-<harness>.stderr.txt
        │       │   └── copilot-logs/    # Copilot only
        │       └── validation/
        └── workspaces/                  # only when retained
```

The harness/model hierarchy intentionally replaces historical model-only
paths. Manifest schema 2, aggregate results schema 7, target results schema 2,
and preflight schema 4 identify both harness and model. Historical artifacts
are not migrated.

Standalone preflight writes `runs/<run-id>/preflight.json` with schema `1`,
`report_type: standalone-preflight`, mode (`agents`, `permissions`, or
`combined`), aggregate status, and nullable `agents` and `permissions`
components. Agent component schema `1` records immutable
harness/model/status/duration/reason/evidence results. The permissions
component embeds the unchanged Azure preflight schema `4`. Command evidence
paths point to captured metadata, stdout, and stderr; console summaries do not
print authentication output.

Copilot evidence contains its JSONL output and session logs. Claude evidence
contains stream JSON; `--no-session-persistence` prevents resumable Claude
sessions outside the evidence directory. Codex evidence contains the
ephemeral `codex exec --json` JSONL stream.

## Run tests

Unit tests use fake agent executables and do not invoke real coding-agent CLIs
or create Azure resources:

```bash
python -m unittest discover -s tests -v
```
