#!/usr/bin/env bash
# Runs the smoke test inside a template brought up by build.sh, then tears the stack down.
# Usage: test.sh <template-id>   (same environment as build.sh)
#
# SMOKE_NO_NPM_REGISTRY=1 skips, and reports as skipped, the npm steps (for networks that block
# registry.npmjs.org). CI never sets it.
set -euo pipefail
source "$(dirname "$0")/common.sh"
trap teardown EXIT
if [ -z "$WS" ]; then
    echo "No workspace recorded at $POINTER; run build.sh first" >&2
    exit 1
fi

# S18: the LocalDev profile's own values, as VS Code would write them into Machine settings.json.
profile=$($DEVCONTAINER read-configuration --workspace-folder "$WS" |
    jq -c '.configuration.customizations.vscode.settings."mssql.connections"[] | select(.profileName == "LocalDev")')

DB_CONTAINER=$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT" --filter "label=com.docker.compose.service=db")
if [ -z "$DB_CONTAINER" ]; then
    echo "No running Azure SQL database container in compose project $PROJECT" >&2
    exit 1
fi
DB_ARCH=$(docker image inspect --format '{{.Architecture}}' "$(docker inspect --format '{{.Image}}' "$DB_CONTAINER")")

$DEVCONTAINER exec --workspace-folder "$WS" \
    --remote-env "PROFILE_SERVER=$(jq -r .server <<<"$profile")" \
    --remote-env "PROFILE_USER=$(jq -r .user <<<"$profile")" \
    --remote-env "PROFILE_PASSWORD=$(jq -r .password <<<"$profile")" \
    --remote-env "PROFILE_DATABASE=$(jq -r .database <<<"$profile")" \
    --remote-env "DB_ARCH=$DB_ARCH" \
    --remote-env "EXPECTED_ARCH=$EXPECTED_ARCH" \
    --remote-env "EXPECTED_DOCKER_ARCH=$ARCH" \
    --remote-env "EXPECTED_DOTNET_MAJOR=$EXPECTED_DOTNET_MAJOR" \
    --remote-env "SMOKE_NO_NPM_REGISTRY=${SMOKE_NO_NPM_REGISTRY:-}" \
    bash test-smoke/test.sh "$TEMPLATE_ID"
