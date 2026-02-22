#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGETS=(
  "architecture/system-architecture.md"
  "architecture/service-boundaries.md"
  "architecture/deployment-topology.md"
  "docs/agent-harness"
  "plans/system/EPIC-SYS-001-harness-radar"
)

PATTERN='TODO:|\[NEEDS CLARIFICATION|\[NEEDS\s+CLARIFICATION'

if command -v rg >/dev/null 2>&1; then
  MATCH_CMD=(rg -n -e "$PATTERN" "${TARGETS[@]}")
else
  MATCH_CMD=(grep -R -n -E "$PATTERN" "${TARGETS[@]}")
fi

if "${MATCH_CMD[@]}"; then
  echo "ERROR: doc gardening failed due to unresolved placeholders." >&2
  exit 1
fi

uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden >/dev/null

echo "doc-gardening: OK"
