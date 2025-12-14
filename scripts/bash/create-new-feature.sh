#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
    cat <<'EOF'
Usage: create-new-feature.sh --feature-id <F-XXX-YYY> [options] <feature description>

Options:
  --feature-id <ID>   Target feature ID defined in harness/feature_list.json
  --short-name <slug> Optional short slug for branch naming (fallbacks: description, feature title)
  --service <name>    Filter candidate features by owning service (repeatable)
  --search <text>     Filter candidate features by substring in ID/title
  --json              Emit machine-readable JSON summary
  --help, -h          Show this message

Example:
  scripts/bash/create-new-feature.sh --feature-id F-API-001 "Implement GET /health spec"
EOF
}

JSON_MODE=false
FEATURE_ID="${FEATURE_ID:-}"
SHORT_NAME=""
FILTER_SERVICES=()
SEARCH_TERM=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --feature-id)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Error: --feature-id requires a value" >&2
                exit 1
            fi
            FEATURE_ID="$1"
            shift
            ;;
        --short-name)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Error: --short-name requires a value" >&2
                exit 1
            fi
            SHORT_NAME="$1"
            shift
            ;;
        --service)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Error: --service requires a value" >&2
                exit 1
            fi
            FILTER_SERVICES+=("$1")
            shift
            ;;
        --search|--title-like)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Error: --search requires a value" >&2
                exit 1
            fi
            SEARCH_TERM="$1"
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

FEATURE_DESCRIPTION="${ARGS[*]}"

if [[ -z "$FEATURE_ID" ]]; then
    if [[ -n "${SPECIFY_FEATURE:-}" && "${SPECIFY_FEATURE}" =~ ^F-[A-Za-z0-9-]+$ ]]; then
        FEATURE_ID="$SPECIFY_FEATURE"
    else
        SERVICE_ARG="$(IFS=,; echo "${FILTER_SERVICES[*]}")"
        FIND_RESULT="$(python3 - "$REPO_ROOT" "$SERVICE_ARG" "$SEARCH_TERM" <<'PY'
import json, os, sys

repo_root = sys.argv[1]
service_csv = sys.argv[2]
search_term = sys.argv[3].strip().lower()
services = [s.strip().lower() for s in service_csv.split(',') if s.strip()]

feature_file = os.path.join(repo_root, "harness", "feature_list.json")
with open(feature_file, encoding="utf-8") as fh:
    raw_lines = [line for line in fh.readlines() if not line.lstrip().startswith("//")]
data = json.loads("".join(raw_lines))

matches = []
for feat in data.get("features", []):
    fid = str(feat.get("id", "")).upper()
    title = feat.get("title", "")
    svc_list = [s.lower() for s in feat.get("services", [])]

    if services and not any(s in svc_list for s in services):
        continue

    if search_term:
        hay = f"{fid} {title}".lower()
        if search_term not in hay:
            continue

    matches.append((fid, title, feat.get("spec_path", ""), feat.get("services", [])))

if not matches:
    print("ERROR=No feature matches. Use --feature-id or narrow filters.")
    sys.exit(0)

if len(matches) > 1:
    print("ERROR=Multiple features match. Use --feature-id to disambiguate.")
    for fid, title, spec_path, svc in matches:
        services = ",".join(svc)
        print(f"CANDIDATE={fid}|{title}|{services}|{spec_path}")
    sys.exit(0)

fid, *_ = matches[0]
print(f"FEATURE_ID={fid}")
PY
)"
        if echo "$FIND_RESULT" | grep -q '^ERROR='; then
            echo "$FIND_RESULT" | grep '^ERROR=' | cut -d'=' -f2- >&2
            if echo "$FIND_RESULT" | grep -q '^CANDIDATE='; then
                echo "$FIND_RESULT" | grep '^CANDIDATE=' | sed 's/^CANDIDATE=/  - /' >&2
            fi
            exit 1
        fi
        FEATURE_ID="$(echo "$FIND_RESULT" | grep '^FEATURE_ID=' | cut -d'=' -f2-)"
        if [[ -z "$FEATURE_ID" ]]; then
            echo "Error: Unable to determine feature ID." >&2
            exit 1
        fi
    fi
fi

FEATURE_ID="$(echo "$FEATURE_ID" | tr '[:lower:]' '[:upper:]')"

HARNESS_FILE="$REPO_ROOT/harness/feature_list.json"
if [[ ! -f "$HARNESS_FILE" ]]; then
    echo "Error: $HARNESS_FILE not found" >&2
    exit 1
fi

META_RAW="$(
    python3 - "$REPO_ROOT" "$FEATURE_ID" <<'PY'
import json, os, sys, base64

repo_root = sys.argv[1]
target = sys.argv[2].upper()
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
    print(f"ERROR=Feature ID {target} is missing spec_path in harness/feature_list.json")
    sys.exit(0)
spec_path = os.path.normpath(os.path.join(repo_root, spec_rel))

default_checklist = os.path.join(os.path.dirname(spec_rel), "checklists", "requirements.md")
checklist_rel = selected.get("checklist_path") or default_checklist
checklist_path = os.path.normpath(os.path.join(repo_root, checklist_rel))

epic_id = selected.get("epic_id", "")
title = selected.get("title", target)
services = ",".join(selected.get("services", []))

print(f"SPEC_PATH={spec_path}")
print(f"CHECKLIST_PATH={checklist_path}")
print(f"FEATURE_TITLE_B64={base64.b64encode(title.encode('utf-8')).decode('ascii')}")
print(f"SERVICES={services}")
print(f"EPIC_ID={epic_id}")
PY
)"

if echo "$META_RAW" | grep -q '^ERROR='; then
    echo "$META_RAW" | grep '^ERROR=' | cut -d'=' -f2- >&2
    exit 1
fi

SPEC_PATH=""
CHECKLIST_PATH=""
FEATURE_TITLE=""
SERVICES=""
EPIC_ID=""

while IFS='=' read -r key value; do
    case "$key" in
        SPEC_PATH) SPEC_PATH="$value" ;;
        CHECKLIST_PATH) CHECKLIST_PATH="$value" ;;
        FEATURE_TITLE_B64) FEATURE_TITLE="$(printf '%s' "$value" | base64 --decode)" ;;
        SERVICES) SERVICES="$value" ;;
        EPIC_ID) EPIC_ID="$value" ;;
    esac
done <<< "$META_RAW"

FEATURE_DIR="$(dirname "$SPEC_PATH")"
CHECKLIST_DIR="$(dirname "$CHECKLIST_PATH")"
mkdir -p "$FEATURE_DIR"
mkdir -p "$CHECKLIST_DIR"

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

trim() {
    local str="$1"
    str="${str#"${str%%[![:space:]]*}"}"
    str="${str%"${str##*[![:space:]]}"}"
    echo "$str"
}

BRANCH_PREFIX=""
if [[ "$FEATURE_ID" =~ ([0-9]{3,})$ ]]; then
    BRANCH_PREFIX="${BASH_REMATCH[1]}"
fi

if [[ -n "$SHORT_NAME" ]]; then
    BRANCH_SUFFIX="$(slugify "$SHORT_NAME")"
elif [[ -n "$FEATURE_DESCRIPTION" ]]; then
    BRANCH_SUFFIX="$(slugify "$FEATURE_DESCRIPTION")"
elif [[ -n "$FEATURE_TITLE" ]]; then
    BRANCH_SUFFIX="$(slugify "$FEATURE_TITLE")"
else
    BRANCH_SUFFIX="feature"
fi

if [[ -z "$BRANCH_SUFFIX" ]]; then
    BRANCH_SUFFIX="feature"
fi

if [[ -n "$BRANCH_PREFIX" ]]; then
    BRANCH_NAME="${BRANCH_PREFIX}-${BRANCH_SUFFIX}"
else
    BRANCH_NAME="${FEATURE_ID,,}-${BRANCH_SUFFIX}"
fi

MAX_BRANCH_LENGTH=244
if [[ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]]; then
    BRANCH_NAME="${BRANCH_NAME:0:$MAX_BRANCH_LENGTH}"
    BRANCH_NAME="$(echo "$BRANCH_NAME" | sed 's/-$//')"
fi

HAS_GIT=false
if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    HAS_GIT=true
    cd "$REPO_ROOT"
    if git rev-parse --verify "refs/heads/$BRANCH_NAME" >/dev/null 2>&1; then
        git checkout "$BRANCH_NAME" >/dev/null 2>&1 || echo "[create-new-feature] Warning: could not checkout existing branch $BRANCH_NAME" >&2
    else
        git checkout -b "$BRANCH_NAME" >/dev/null 2>&1 || echo "[create-new-feature] Warning: could not create branch $BRANCH_NAME" >&2
    fi
else
    echo "[create-new-feature] Warning: Git repository not detected; branch creation skipped." >&2
fi

DATE_UTC="$(date -u +"%Y-%m-%d")"
DESC_TEXT="$(trim "${FEATURE_DESCRIPTION:-Feature description not provided}")"

SPEC_TEMPLATE="$REPO_ROOT/templates/spec-template.md"
if [[ ! -f "$SPEC_PATH" ]]; then
    if [[ -f "$SPEC_TEMPLATE" ]]; then
        cp "$SPEC_TEMPLATE" "$SPEC_PATH"
    else
        cat <<'EOF' > "$SPEC_PATH"
# Feature Specification

EOF
    fi
    SPEC_TEMPLATE_FEATURE_TITLE="$FEATURE_TITLE" \
    SPEC_TEMPLATE_FEATURE_ID="$FEATURE_ID" \
    SPEC_TEMPLATE_BRANCH_NAME="$BRANCH_NAME" \
    SPEC_TEMPLATE_DESC="$DESC_TEXT" \
    SPEC_TEMPLATE_DATE="$DATE_UTC" \
    python3 - "$SPEC_PATH" <<'PY'
import os, sys
path = sys.argv[1]
title = os.environ.get("SPEC_TEMPLATE_FEATURE_TITLE", "").strip() or "[FEATURE NAME]"
fid = os.environ.get("SPEC_TEMPLATE_FEATURE_ID", "").strip() or "[F-XXX-YYY]"
branch = os.environ.get("SPEC_TEMPLATE_BRANCH_NAME", "").strip() or "[###-feature-name]"
desc = os.environ.get("SPEC_TEMPLATE_DESC", "").strip()
if not desc:
    desc = "Not provided"
date_str = os.environ.get("SPEC_TEMPLATE_DATE", "").strip() or "[DATE]"

with open(path, encoding="utf-8") as fh:
    content = fh.read()

content = (
    content.replace("[FEATURE NAME]", title, 1)
           .replace("[F-XXX-YYY]", fid, 1)
           .replace("[###-feature-name]", branch, 1)
           .replace("[DATE]", date_str, 1)
           .replace("$ARGUMENTS", desc, 1)
)

with open(path, "w", encoding="utf-8") as fh:
    fh.write(content)
PY
else
    echo "[create-new-feature] Spec already exists at $SPEC_PATH; leaving untouched." >&2
fi

if [[ ! -f "$CHECKLIST_PATH" ]]; then
    cat <<EOF > "$CHECKLIST_PATH"
# ${FEATURE_ID} Requirements Checklist

**Created**: ${DATE_UTC}  
**Feature**: ${FEATURE_TITLE}

## Content Quality
- [ ] No [NEEDS CLARIFICATION] markers remain in spec.md
- [ ] Requirements are testable and free from implementation details
- [ ] Scope boundaries and success criteria are clearly written

## Acceptance Readiness
- [ ] User stories in spec.md have measurable acceptance scenarios
- [ ] Edge cases and error states are captured in the specification
- [ ] Dependencies and assumptions are documented
EOF
else
    echo "[create-new-feature] Checklist already exists at $CHECKLIST_PATH; leaving untouched." >&2
fi

export SPECIFY_FEATURE="$FEATURE_ID"

if $JSON_MODE; then
    python3 - <<'PY' "$BRANCH_NAME" "$SPEC_PATH" "$FEATURE_ID" "$FEATURE_DIR" "$CHECKLIST_PATH" "$EPIC_ID" "$FEATURE_TITLE"
import json, sys
keys = [
    "BRANCH_NAME",
    "SPEC_FILE",
    "FEATURE_ID",
    "FEATURE_DIR",
    "CHECKLIST_FILE",
    "EPIC_ID",
    "FEATURE_TITLE",
]
data = dict(zip(keys, sys.argv[1:]))
print(json.dumps(data))
PY
else
    cat <<EOF
Feature ID     : $FEATURE_ID
Spec file      : $SPEC_PATH
Checklist file : $CHECKLIST_PATH
Feature dir    : $FEATURE_DIR
Branch name    : $BRANCH_NAME
Epic ID        : ${EPIC_ID:-N/A}
Services       : ${SERVICES:-N/A}
SPECIFY_FEATURE environment variable set to: $FEATURE_ID
EOF
fi
