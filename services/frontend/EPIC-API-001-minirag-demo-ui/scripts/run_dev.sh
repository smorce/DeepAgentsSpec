#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PORT="${PORT:-5173}"

if command -v uv >/dev/null 2>&1; then
  uv run --link-mode=copy python -m http.server "${PORT}" --directory "${ROOT_DIR}/public"
else
  python -m http.server "${PORT}" --directory "${ROOT_DIR}/public"
fi
