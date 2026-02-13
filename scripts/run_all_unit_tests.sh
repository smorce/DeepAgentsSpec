#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mapfile -t TEST_SCRIPTS < <(find services -type f -path "*/scripts/run_unit_tests.sh" | sort)

if [ "${#TEST_SCRIPTS[@]}" -eq 0 ]; then
  echo "[run_all_unit_tests.sh] No unit test scripts were found under services/." >&2
  exit 1
fi

for test_script in "${TEST_SCRIPTS[@]}"; do
  echo "[run_all_unit_tests.sh] Running: ${test_script}"
  bash "$test_script"
done

echo "[run_all_unit_tests.sh] Completed (${#TEST_SCRIPTS[@]} scripts)."
