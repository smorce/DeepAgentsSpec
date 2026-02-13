#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[format_or_lint.sh] Checking shell script syntax..."
mapfile -t SHELL_FILES < <(find scripts harness services -type f -name "*.sh" | sort)
for shell_file in "${SHELL_FILES[@]}"; do
  bash -n "$shell_file"
done

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN=""
fi

if [ -n "$PYTHON_BIN" ]; then
  echo "[format_or_lint.sh] Checking Python syntax..."
  "$PYTHON_BIN" -m py_compile harness/agent_radar/radar_ops.py
else
  echo "[format_or_lint.sh] WARN: python executable is not available. Skipping Python syntax check."
fi

echo "[format_or_lint.sh] Checking unresolved placeholders in core docs..."
bash scripts/garden_agent_docs.sh

echo "[format_or_lint.sh] All checks passed."
