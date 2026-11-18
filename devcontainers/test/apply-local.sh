#!/usr/bin/env bash
# Applies an unpublished template from this checkout to an empty workspace.
# Usage: apply-local.sh <template-id> <empty-workspace> [imageVariant]
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TEMPLATE_ID=${1:?usage: $0 <template-id> <empty-workspace> [imageVariant]}
DEST=${2:?usage: $0 <template-id> <empty-workspace> [imageVariant]}
TEMPLATE=$ROOT/devcontainers/src/$TEMPLATE_ID
if [ ! -f "$TEMPLATE/devcontainer-template.json" ]; then
    echo "Unknown template: $TEMPLATE_ID" >&2
    exit 2
fi

mkdir -p "$DEST"
if [ -n "$(find "$DEST" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    echo "Workspace must be empty: $DEST" >&2
    exit 2
fi

for key in $(jq -r '.options | keys[]' "$TEMPLATE/devcontainer-template.json"); do
    value=$(jq -er --arg key "$key" '.options[$key].default' "$TEMPLATE/devcontainer-template.json")
    if [ "$key" = imageVariant ] && [ -n "${3:-}" ]; then
        value=$3
    fi
    jq -e --arg key "$key" --arg value "$value" '.options[$key].proposals | index($value)' \
        "$TEMPLATE/devcontainer-template.json" >/dev/null
done

cp -R "$TEMPLATE/." "$DEST/"
rm -f "$DEST/devcontainer-template.json" "$DEST/README.md" "$DEST/NOTES.md"
for key in $(jq -r '.options | keys[]' "$TEMPLATE/devcontainer-template.json"); do
    value=$(jq -er --arg key "$key" '.options[$key].default' "$TEMPLATE/devcontainer-template.json")
    if [ "$key" = imageVariant ] && [ -n "${3:-}" ]; then value=$3; fi
    grep -rlIF "\${templateOption:$key}" "$DEST" | while IFS= read -r file; do
        KEY=$key VALUE=$value perl -pi -e 's/\$\{templateOption:\Q$ENV{KEY}\E\}/$ENV{VALUE}/g' "$file"
    done
done

# shellcheck disable=SC2016 # Match the literal template placeholder syntax.
if grep -rnIF '${templateOption:' "$DEST"; then
    echo "Unsubstituted template option (above)" >&2
    exit 1
fi
echo "Applied $TEMPLATE_ID to $DEST"
