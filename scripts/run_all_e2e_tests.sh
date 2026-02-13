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

# UIシナリオは静的配信とAPIモックを内包しているため常時実行する。
node "${ROOT_DIR}/tests/e2e/scenarios/minirag_demo_ui.spec.js"

# live APIシナリオはバックエンド起動が前提のため、明示指定時のみ実行する。
if [ "${RUN_LIVE_MINIRAG_E2E:-0}" = "1" ]; then
  node "${ROOT_DIR}/tests/e2e/scenarios/minirag_demo.spec.js"
else
  echo "[run_all_e2e_tests.sh] Skipping live API scenario. Set RUN_LIVE_MINIRAG_E2E=1 to enable."
fi
