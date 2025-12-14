#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/templates/checklist"

usage() {
    cat <<'EOF'
Usage: add-domain-checklist.sh --template <name> [options]

Options:
  --feature-id <ID>   Feature ID in harness/feature_list.json (defaults to $SPECIFY_FEATURE)
  --template <name>   Template file name or slug under templates/checklist (required)
  --output <file>     Destination filename (default: <template-slug>.md)
  --force             Overwrite existing file
  --list              List available templates
  --json              Emit machine-readable output
  --help, -h          Show this message

Example:
  scripts/bash/add-domain-checklist.sh --feature-id F-API-001 --template "統合セキュリティガイドライン チェックリスト"
EOF
}

list_templates() {
    echo "Available templates:"
    find "$TEMPLATE_DIR" -maxdepth 1 -type f -name '*.md' -print | sort | while read -r path; do
        base="$(basename "$path")"
        echo "  - $base"
    done
}

JSON_MODE=false
FEATURE_ID="${FEATURE_ID:-}"
TEMPLATE_KEY=""
OUTPUT_NAME=""
FORCE=false
LIST_ONLY=false
ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --feature-id)
            shift
            [[ $# -gt 0 ]] || { echo "Error: --feature-id requires a value" >&2; exit 1; }
            FEATURE_ID="$1"
            shift
            ;;
        --template)
            shift
            [[ $# -gt 0 ]] || { echo "Error: --template requires a value" >&2; exit 1; }
            TEMPLATE_KEY="$1"
            shift
            ;;
        --output)
            shift
            [[ $# -gt 0 ]] || { echo "Error: --output requires a value" >&2; exit 1; }
            OUTPUT_NAME="$1"
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --list)
            LIST_ONLY=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --*)
            echo "Error: Unknown option $1" >&2
            exit 1
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

if $LIST_ONLY; then
    list_templates
    exit 0
fi

if [[ -z "$TEMPLATE_KEY" ]]; then
    echo "Error: --template is required" >&2
    usage
    exit 1
fi

if [[ -z "$FEATURE_ID" ]]; then
    if [[ -n "${SPECIFY_FEATURE:-}" && "${SPECIFY_FEATURE}" =~ ^F-[A-Za-z0-9-]+$ ]]; then
        FEATURE_ID="$SPECIFY_FEATURE"
    else
        echo "Error: --feature-id is required (or set SPECIFY_FEATURE)" >&2
        exit 1
    fi
fi

FEATURE_ID="${FEATURE_ID^^}"

resolve_template_path() {
    local key="$1"
    local path=""
    if [[ -f "$key" ]]; then
        path="$key"
    else
        local exact="$TEMPLATE_DIR/$key"
        if [[ -f "$exact" ]]; then
            path="$exact"
        else
            while IFS= read -r candidate; do
                if [[ "${candidate##*/}" =~ ${key// /.*} ]]; then
                    path="$candidate"
                    break
                fi
            done < <(find "$TEMPLATE_DIR" -maxdepth 1 -type f -name '*.md')
        fi
    fi
    echo "$path"
}

TEMPLATE_PATH="$(resolve_template_path "$TEMPLATE_KEY")"
if [[ -z "$TEMPLATE_PATH" ]]; then
    echo "Error: Template '$TEMPLATE_KEY' not found under $TEMPLATE_DIR" >&2
    list_templates >&2
    exit 1
fi

HARNESS_FILE="$REPO_ROOT/harness/feature_list.json"
if [[ ! -f "$HARNESS_FILE" ]]; then
    echo "Error: $HARNESS_FILE not found" >&2
    exit 1
fi

META_RAW="$(
python3 - "$REPO_ROOT" "$FEATURE_ID" <<'PY'
import json, os, sys

repo_root = sys.argv[1]
target = sys.argv[2]
feature_file = os.path.join(repo_root, "harness", "feature_list.json")

with open(feature_file, encoding="utf-8") as fh:
    raw_lines = [line for line in fh.readlines() if not line.lstrip().startswith("//")]
data = json.loads("".join(raw_lines))

selected = None
for feat in data.get("features", []):
    if str(feat.get("id", "")).upper() == target:
        selected = feat
        break

if not selected:
    print(f"ERROR=Feature ID {target} not found in harness/feature_list.json")
    sys.exit(0)

spec_rel = selected.get("spec_path")
if not spec_rel:
    print(f"ERROR=Feature {target} is missing spec_path")
    sys.exit(0)

spec_abs = os.path.normpath(os.path.join(repo_root, spec_rel))
feature_dir = os.path.dirname(spec_abs)
title = selected.get("title", target)
print(f"FEATURE_DIR={feature_dir}")
print(f"FEATURE_TITLE={title}")
PY
)"

if echo "$META_RAW" | grep -q '^ERROR='; then
    echo "$META_RAW" | grep '^ERROR=' | cut -d'=' -f2- >&2
    exit 1
fi

FEATURE_DIR=""
FEATURE_TITLE=""
while IFS='=' read -r key value; do
    case "$key" in
        FEATURE_DIR) FEATURE_DIR="$value" ;;
        FEATURE_TITLE) FEATURE_TITLE="$value" ;;
    esac
done <<< "$META_RAW"

DEST_DIR="$FEATURE_DIR/checklists"
mkdir -p "$DEST_DIR"

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/-{2,}/-/g; s/^-//; s/-$//'
}

if [[ -z "$OUTPUT_NAME" ]]; then
    base="$(basename "$TEMPLATE_PATH")"
    OUTPUT_NAME="${base%.md}.md"
fi

[[ "$OUTPUT_NAME" == *.md ]] || OUTPUT_NAME+=".md"
DEST_PATH="$DEST_DIR/$OUTPUT_NAME"

if [[ -f "$DEST_PATH" && $FORCE == false ]]; then
    echo "Error: $DEST_PATH already exists. Use --force to overwrite." >&2
    exit 1
fi

cp "$TEMPLATE_PATH" "$DEST_PATH"

DATE_UTC="$(date -u +"%Y-%m-%d")"

python3 - "$DEST_PATH" "$FEATURE_TITLE" "$FEATURE_ID" "$DATE_UTC" <<'PY'
import sys
path, title, fid, date_str = sys.argv[1:5]

with open(path, encoding="utf-8") as fh:
    content = fh.read()

content = (content
    .replace("[FEATURE NAME]", title)
    .replace("[FEATURE-ID]", fid)
    .replace("[DATE]", date_str)
)

with open(path, "w", encoding="utf-8") as fh:
    fh.write(content)
PY

if $JSON_MODE; then
    python3 - <<'PY' "$DEST_PATH" "$TEMPLATE_PATH" "$FEATURE_ID"
import json, sys
dest, src, fid = sys.argv[1:4]
print(json.dumps({
    "feature_id": fid,
    "template": src,
    "output": dest
}))
PY
else
    cat <<EOF
Checklist created:
  Feature ID : $FEATURE_ID
  Template   : $TEMPLATE_PATH
  Output     : $DEST_PATH
EOF
fi
