#!/usr/bin/env bash

set -euo pipefail

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required to run E2E tests." >&2
  exit 1
fi

node tests/e2e/scenarios/minirag_demo.spec.js
