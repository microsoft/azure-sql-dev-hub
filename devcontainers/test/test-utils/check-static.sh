#!/usr/bin/env bash
# Promises every change must keep, checked without Docker. Runs in CI's static job and the local gauntlet.
#   Template ids and Azure SQL target, unchanged SQL schema/data, Library LocalDev profile, native platform
#   selection, compose shape, and full database CI integrity on AMD64 and ARM64.
# Needs jq, ruby (YAML), and shasum. Usage: check-static.sh [repo-dir]
set -euo pipefail

cd "${1:-$(dirname "$0")/../../..}"
TEMPLATES="dotnet dotnet-aspire javascript-node python"
WORKFLOW=.github/workflows/devcontainer-tests.yml
ACTION=.github/actions/devcontainer-smoke-test/action.yaml
RELEASE=.github/workflows/devcontainer-release.yml
failures=0
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

ok() { echo "ok: $*"; }
bad() { echo "FAILED: $*" >&2; failures=$((failures + 1)); }
# expect LABEL CMD...: CMD must exit 0.
expect() {
    local label=$1
    shift
    if "$@"; then ok "$label"; else bad "$label"; fi
}
# The workflow uses YAML anchors. Psych 4 (Ruby 3.1+) refuses aliases unless asked; Psych 3 has no
# such keyword and raises ArgumentError for it, so try the new signature and fall back to the old.
yaml2json() {
    ruby -ryaml -rjson -e '
        begin
            doc = YAML.load_file(ARGV[0], aliases: true)
        rescue ArgumentError
            doc = YAML.load_file(ARGV[0])
        end
        puts JSON.generate(doc)' "$1"
}

# --- M1, M2, M3 ---------------------------------------------------------------------------------------------
idsUnchanged() {
    local t
    [ "$(for t in devcontainers/src/*/devcontainer-template.json; do jq -r .id "$t"; done | sort | paste -sd' ' -)" = "$TEMPLATES" ] || return 1
    for t in $TEMPLATES; do [ "$(jq -r .id "devcontainers/src/$t/devcontainer-template.json")" = "$t" ] || return 1; done
}
dspUnchanged() {
    local t
    for t in $TEMPLATES; do
        [ "$(grep -c '<DSP>Microsoft.Data.Tools.Schema.Sql.SqlAzureV12DatabaseSchemaProvider</DSP>' "devcontainers/src/$t/database/Library/Library.sqlproj")" = 1 ] || return 1
    done
}
sqlUnchanged() { # every source .sql file matches the committed manifest, and there are no others
    shasum -a 256 -c devcontainers/test/fixtures/library-sql.sha256 >"$tmp/sql.txt" || { grep -v ': OK$' "$tmp/sql.txt" >&2; return 1; }
    [ "$(git -c core.quotePath=false ls-files ':(glob)devcontainers/src/*/database/Library/**/*.sql' | wc -l)" -eq "$(wc -l <devcontainers/test/fixtures/library-sql.sha256)" ]
}
expect "M1 template ids are dotnet, dotnet-aspire, javascript-node, python" idsUnchanged
expect "M2 all 4 SQL projects target SqlAzureV12DatabaseSchemaProvider" dspUnchanged
expect "M3 the 28 Library .sql files match test/fixtures/library-sql.sha256" sqlUnchanged

# --- M7 and the compose shape ---------------------------------------------------------------------------------
localDev() { # TEMPLATE
    local workspace="$tmp/workspace-$1"
    local config="$workspace/.devcontainer/devcontainer.json"
    devcontainers/test/apply-local.sh "$1" "$workspace" >/dev/null || return 1
    # Apply template options before parsing the JSONC and checking the LocalDev settings.
    # The profile carries ${containerEnv:MSSQL_SA_PASSWORD}: the dev container CLI resolves it from the
    # container's environment at create time, so the password itself lives only in .env. ${env:...} does
    # NOT resolve (measured: it arrives as an empty string), and a literal password here would duplicate .env.
    sed -n 's/^MSSQL_SA_PASSWORD=//p' "$workspace/.devcontainer/.env" | grep -q . || return 1
    sed '/^[[:space:]]*\/\//d' "$config" | jq -e '
        (.customizations.vscode.settings."mssql.connections"[]
            | select(.profileName == "LocalDev")
            | .password == "${containerEnv:MSSQL_SA_PASSWORD}" and .database == "Library" and .savePassword == true)
        and (.forwardPorts | index(1433))
        and (.customizations.vscode.extensions | index("ms-mssql.mssql"))
        and any(.customizations.vscode.settings."mssql.connections"[]; .profileName == "LocalDev" and .server == "localhost,1433" and .database == "Library")' >/dev/null
}
composeShape() { # TEMPLATE
    yaml2json "devcontainers/src/$1/.devcontainer/docker-compose.yml" | jq -e '(has("version") | not)
        and .services.db.image == "mcr.microsoft.com/mssql/azure-sql-db-server:latest"
        and (.services.db | has("platform") | not)
        and (.services.db.environment | has("MSSQL_PID") | not)
        and .services.db.restart == "unless-stopped"
        and (.services.db.healthcheck.test | tostring | contains("/opt/mssql-tools18/bin/sqlcmd"))
        and .services.db.deploy.resources.limits == {"cpus": "2", "memory": "2048M"}
        and (.services.db | has("container_name") | not)
        and .services.app.depends_on.db.condition == "service_healthy"
        and .services.app.network_mode == "service:db"' >/dev/null
}
for t in $TEMPLATES; do
    expect "M7/S18 $t: applied template configures LocalDev from .env on localhost,1433, port 1433 with ms-mssql.mssql" localDev "$t"
    expect "compose $t: Azure SQL, native platform, restart, healthcheck, 2 CPU/2048M, app waits for healthy" composeShape "$t"
done

# --- S15: CI integrity ----------------------------------------------------------------------------------------
yaml2json "$WORKFLOW" >"$tmp/workflow.json"
yaml2json "$ACTION" >"$tmp/action.json"

pinned() {
    local files
    files=$(git ls-files "$WORKFLOW" "$ACTION" "$RELEASE")
    [ -n "$files" ] && [ "$(printf '%s\n' "$files" | xargs grep -hE '^\s*-?\s*uses:' | grep -vcE 'uses: (\./|[^@]+@[0-9a-f]{40}( |$))')" = 0 ]
}
triggers() {
    jq -e '(.true | has("pull_request") and has("schedule") and has("workflow_dispatch"))
        and .permissions == {"contents": "read", "pull-requests": "read"}
        and .jobs.test.strategy.matrix.runner == ["ubuntu-latest", "ubuntu-24.04-arm"]' "$tmp/workflow.json" >/dev/null
}
# Only these conditions may appear; `if: false` or any other condition on a job or step fails.
conditions() {
    [ "$(jq -c '[.. | objects | select(has("if")) | .if]' "$tmp/workflow.json" "$tmp/action.json" | paste -sd' ' -)" = \
        "[\"github.event_name == 'pull_request'\",\"needs.detect-changes.outputs.templates != '[]'\"] []" ]
}
noContinueOnError() { jq -e '[.. | objects | select(has("continue-on-error"))] | length == 0' "$tmp/workflow.json" "$tmp/action.json" >/dev/null; }
# No step may swallow a failure.
noSwallowedFailures() {
    local runs
    runs=$(jq -r '.. | objects | .run? // empty' "$tmp/workflow.json" "$tmp/action.json") || return 2
    [ -n "$runs" ] || return 2
    ! grep -nE '\|\||set[[:space:]]+\+[a-z]*e|exit[[:space:]]+0|;[[:space:]]*true' <<<"$runs"
}
# Both native architecture runners use the same action, which always runs the full database suite.
smokeStep() {
    jq -e '[.jobs.test.steps[] | select(.uses == "./.github/actions/devcontainer-smoke-test")]
        | length == 1 and .[0].with.template == "${{ matrix.template }}" and (.[0].with | has("mode") | not)' "$tmp/workflow.json" >/dev/null
}
actionRuns() {
    local want
    # shellcheck disable=SC2016 # the literal run strings of the action
    want='["\"$GITHUB_ACTION_PATH/build.sh\" \"$TEMPLATE\"","\"$GITHUB_ACTION_PATH/test.sh\" \"$TEMPLATE\""]'
    [ "$(jq -c '[.runs.steps[].run]' "$tmp/action.json")" = "$want" ] || return 1
    jq -e '.runs.steps | all(.env.TEMPLATE == "${{ inputs.template }}")' "$tmp/action.json" >/dev/null
    jq -e '(.inputs | keys) == ["template"]' "$tmp/action.json" >/dev/null
}
# The Pick step, executed: a pull request picks the changed templates; schedule and dispatch pick all four.
pick() { # EVENT CHANGES -> templates JSON
    local out="$tmp/pick-output"
    : >"$out"
    EVENT=$1 CHANGES=$2 GITHUB_OUTPUT=$out bash -euo pipefail -c "$(jq -r '.jobs["detect-changes"].steps[] | select(.id == "pick") | .run' "$tmp/workflow.json")"
    sed -n 's/^templates=//p' "$out"
}
pickStep() {
    local all='["dotnet","dotnet-aspire","javascript-node","python"]'
    [ "$(pick pull_request '["python","shared"]')" = '["python"]' ] &&
        [ "$(pick pull_request '["dotnet","dotnet-aspire","javascript-node","python","shared"]')" = "$all" ] &&
        [ "$(pick pull_request '[]')" = '[]' ] &&
        [ "$(pick schedule '')" = "$all" ] &&
        [ "$(pick workflow_dispatch '')" = "$all" ] &&
        jq -e '.jobs.test.strategy.matrix.template == "${{ fromJSON(needs.detect-changes.outputs.templates) }}"' "$tmp/workflow.json" >/dev/null
}
# The static job runs every gate that needs no Docker.
staticJob() {
    local runs
    runs=$(jq -r '.jobs.static.steps[].run // empty' "$tmp/workflow.json")
    for gate in "shellcheck -x -P SCRIPTDIR" devcontainers/test/test-utils/check-shared.sh devcontainers/test/test-utils/check-forbidden.sh devcontainers/test/test-utils/check-static.sh devcontainers/test/test-utils/check-tags.sh; do
        grep -qF -- "$gate" <<<"$runs" || { echo "static job does not run $gate" >&2; return 1; }
    done
}
# filterSelects FILTERS-JSON PATH: the templates the paths filter selects for a change to PATH (bash patterns).
filterSelects() {
    jq -r 'to_entries[] | select(.key != "shared") | .key as $k | .value | flatten[] | "\($k)\t\(.)"' "$1" |
        while IFS="$(printf '\t')" read -r key pattern; do
            # shellcheck disable=SC2053 # the pattern is meant to glob
            if [[ $2 == $pattern ]]; then echo "$key"; fi
        done | sort -u | paste -sd' ' -
}
# checkFilters FILTERS-JSON: a template's own files select it, the shared test files select all four, and other
# files select nothing (13 representative paths).
checkFilters() {
    local path want got all="dotnet dotnet-aspire javascript-node python"
    while IFS='=' read -r path want; do
        got=$(filterSelects "$1" "$path")
        if [ "$got" != "$want" ]; then echo "a change to $path selects '$got', want '$want'" >&2; return 1; fi
    done <<PATHS
devcontainers/src/dotnet/.devcontainer/devcontainer.json=dotnet
devcontainers/src/dotnet-aspire/.devcontainer/devcontainer.json=dotnet-aspire
devcontainers/src/javascript-node/.devcontainer/devcontainer.json=javascript-node
devcontainers/src/python/.devcontainer/devcontainer.json=python
devcontainers/test/dotnet/test.sh=dotnet dotnet-aspire
devcontainers/test/javascript-node/index.js=javascript-node
devcontainers/test/python/test.sh=python
devcontainers/test/test-utils/test-utils.sh=$all
devcontainers/test/apply-local.sh=$all
devcontainers/test/fixtures/azure-incompatible/documents.sql=$all
.github/actions/devcontainer-smoke-test/build.sh=$all
.github/workflows/devcontainer-tests.yml=$all
devcontainers/README.md=
devcontainers/docs/images/x.png=
PATHS
}
pathsFilter() {
    jq -r '.jobs["detect-changes"].steps[] | select(.id == "filter") | .with.filters' "$tmp/workflow.json" >"$tmp/filters.yml"
    yaml2json "$tmp/filters.yml" >"$tmp/filters.json"
    checkFilters "$tmp/filters.json"
}
# A mirror download reaches pip only after its hashes are checked against pypi.org.
wheelsVerified() { grep -qF 'python /smoke/verify_wheels.py /smoke/wheels' .github/actions/devcontainer-smoke-test/build.sh; }

noForcedArchitecture() {
    ! git grep -nE 'platform:[[:space:]]*linux/amd64|FROM[[:space:]]+--platform|--platform[=[:space:]]+linux/amd64|DOCKER_DEFAULT_PLATFORM|PLATFORM=linux/amd64|nodb' \
        -- devcontainers/src .github/actions/devcontainer-smoke-test "$WORKFLOW"
}
databaseCoverage() {
    local template script
    for template in $TEMPLATES; do
        case $template in
            dotnet | dotnet-aspire) script=devcontainers/test/dotnet/test.sh ;;
            *) script="devcontainers/test/$template/test.sh" ;;
        esac
        grep -qFx 'checkDatabase' "$script" || return 1
    done
    grep -qF 'checkEquals "S4 Azure SQL engine edition" 5 masterSql' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'sqlcmd -S localhost -U sa -C -b -h -1 -W -d Library' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'checkLibraryCounts S8' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'check "S8 task 3 re-publishes"' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'check "S18 the LocalDev profile authenticates" profileAuthenticates' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF "SQLCMDPASSWORD=\$PROFILE_PASSWORD sqlcmd" devcontainers/test/test-utils/test-utils.sh &&
        grep -qF -- '-b -h -1 -W -l 5' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'SET NOCOUNT ON; SELECT COUNT(*) FROM dbo.books' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF "grep -q '^24$'" devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'check "S16 a failed build is never published" failedBuildNeverPublishes' devcontainers/test/test-utils/test-utils.sh &&
        grep -qF 'TargetDatabaseName:Library' devcontainers/src/dotnet/.devcontainer/sql/postCreateCommand.sh &&
        grep -qF -- '-d master -Q "IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = N' devcontainers/src/dotnet/.devcontainer/sql/postCreateCommand.sh &&
        grep -qF 'CREATE DATABASE [Library];' devcontainers/src/dotnet/.devcontainer/sql/postCreateCommand.sh
}
releaseIsManual() {
    jq -e '.true | has("workflow_dispatch") and (has("push") | not) and (has("pull_request") | not)' "$tmp/release.json" >/dev/null &&
        jq -e '.permissions == {"contents":"read","packages":"write"} and .jobs.publish.if == "github.ref == '\''refs/heads/main'\''"' "$tmp/release.json" >/dev/null &&
        jq -e '.jobs.publish.steps[] | select(.uses | startswith("devcontainers/action@")) | .with["base-path-to-templates"] == "./devcontainers/src" and .env.GITHUB_TOKEN == "${{ secrets.GITHUB_TOKEN }}"' "$tmp/release.json" >/dev/null
}

expect "S15 actions pinned by commit SHA" pinned
expect "S15 triggers (PR, weekly, manual), permissions, amd64 and arm64 runners" triggers
expect "S15 only the two known job and step conditions" conditions
expect "S15 no continue-on-error" noContinueOnError
expect "S15 no step swallows a failure" noSwallowedFailures
expect "S15 every native architecture matrix entry runs the full database smoke test" smokeStep
expect "S15 the smoke-test action runs build.sh and test.sh as they are" actionRuns
expect "S15 the Pick step selects the changed templates, and all four on schedule and dispatch" pickStep
expect "S15 the static job runs shellcheck, check-shared, check-forbidden, check-static, check-tags" staticJob
expect "S15 paths filter: own, shared, and unrelated files (14 paths)" pathsFilter
expect "mirror wheels are verified before pip may use them" wheelsVerified
expect "S15 every template smoke test retains full database checks" databaseCoverage
expect "native architecture is never forced in template defaults or the normal smoke path" noForcedArchitecture
yaml2json "$RELEASE" >"$tmp/release.json"
expect "release workflow is manual, scoped to main, and uses the built-in token" releaseIsManual

echo "check-static: $failures failure(s)"
[ "$failures" -eq 0 ]
