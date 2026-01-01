#!/usr/bin/env bash

set -euo pipefail

# サービスのルートディレクトリを解決
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/server"

if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: Python is required to run server tests." >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  export UV_LINK_MODE=copy
  (
    cd "$SERVER_DIR"
    uv run --link-mode=copy pytest
  )
else
  (
    cd "$SERVER_DIR"
    python -m pytest
  )
fi
