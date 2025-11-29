#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[init.sh] Repository root: $ROOT_DIR"

echo "[init.sh] This script is a template. Customize it for your stack."

echo "[init.sh] Step 1: Install dependencies (TODO: fill in)"

# Example for Node:
# if [ -f package.json ]; then
#   npm install
# fi

echo "[init.sh] Step 2: Run all unit tests (TODO: fill in)"

# if [ -x scripts/run_all_unit_tests.sh ]; then
#   scripts/run_all_unit_tests.sh
# fi

echo "[init.sh] Step 3: Run all e2e tests (TODO: fill in)"

# if [ -x scripts/run_all_e2e_tests.sh ]; then
#   scripts/run_all_e2e_tests.sh
# fi

echo "[init.sh] Step 4: Start development environment (TODO: fill in)"

# Example:
# docker-compose up -d
# or
# npm run dev

echo "[init.sh] Initialization script completed (template)."

