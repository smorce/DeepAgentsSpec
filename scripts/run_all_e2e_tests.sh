#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "[run_all_e2e_tests.sh] node is not installed. Install Node.js to run E2E tests." >&2
  exit 1
fi

node -e "require('puppeteer')" >/dev/null 2>&1 || {
  echo "[run_all_e2e_tests.sh] puppeteer is not installed. Install it before running E2E tests." >&2
  exit 1
}

node "${ROOT_DIR}/tests/e2e/scenarios/minirag_demo_ui.spec.js"
