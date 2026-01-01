#!/usr/bin/env bash

set -euo pipefail

# サービスのルートディレクトリを解決
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/server"
APP_DIR="$ROOT_DIR/app"

# 前提コマンドの存在確認
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required to run the client." >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required to run the client." >&2
  exit 1
fi
PYTHON_CMD=""
for cmd in python python3 py; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_CMD="$cmd"
    break
  fi
done
if [ -z "$PYTHON_CMD" ]; then
  echo "ERROR: Python is required to run the server (python/python3/py)." >&2
  exit 1
fi

# uv がある場合は uv を使ってサーバーを起動
if command -v uv >/dev/null 2>&1; then
  export UV_LINK_MODE=copy
  SERVER_CMD=(uv run --link-mode=copy "$PYTHON_CMD" main.py)
else
  SERVER_CMD=("$PYTHON_CMD" main.py)
fi

# サーバーをバックグラウンド起動
(
  cd "$SERVER_DIR"
  "${SERVER_CMD[@]}"
) &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# クライアントを起動（Webブラウザのみ）
(
  cd "$APP_DIR"
  export AVATAR_UI_WEB_ONLY=1
  npm run dev
)
