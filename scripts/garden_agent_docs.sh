#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGETS=(
  "architecture/system-architecture.md"
  "architecture/service-boundaries.md"
  "architecture/deployment-topology.md"
  "docs/agent-harness"
  "plans/system/EPIC-SYS-002-harness-radar"
)

PATTERN='TODO:|\[NEEDS CLARIFICATION|\[NEEDS\s+CLARIFICATION'

if rg -n -e "$PATTERN" "${TARGETS[@]}"; then
  echo "ERROR: doc gardening failed due to unresolved placeholders." >&2
  exit 1
fi

echo "doc-gardening: OK"
