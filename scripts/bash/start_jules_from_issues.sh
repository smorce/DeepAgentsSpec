#!/usr/bin/env bash
set -euo pipefail

# Usage: ./start_jules_from_issues.sh [limit] [wait_seconds]
LIMIT="${1:-2}"
WAIT_SECONDS="${2:-${JULES_WAIT_SECONDS:-600}}"

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Error: limit must be a non-negative integer (got: $LIMIT)" >&2
  exit 1
fi
if ! [[ "$WAIT_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "Error: wait_seconds must be a non-negative integer (got: $WAIT_SECONDS)" >&2
  exit 1
fi

# 番号<TAB>タイトル の形式で取得（jq 不要）
issue_lines="$(
  gh issue list \
    --assignee @me \
    --state open \
    --limit "$LIMIT" \
    --json number,title \
    --template '{{range .}}{{.number}}{{"\t"}}{{.title}}{{"\n"}}{{end}}'
)"

if [[ -z "${issue_lines//$'\n'/}" ]]; then
  echo "No open issues assigned to me"
  exit 0
fi

count="$(printf '%s\n' "$issue_lines" | sed '/^$/d' | wc -l | tr -d ' ')"
echo "Starting $count Jules tasks in parallel..."

while IFS=$'\t' read -r number title; do
  [[ -z "${number:-}" ]] && continue

  body="$(
    gh issue view "$number" \
      --json body \
      --template '{{.body}}'
  )"

  prompt=$(cat <<EOF
You are working on the following GitHub Issue.

Issue Number: #$number
Title:
$title

Description:
$body

Please implement this task. Please check out the relevant branch before starting the task.
EOF
)

  echo "→ Starting Jules task for Issue #$number"
  printf '%s\n' "$prompt" | jules remote new --repo . &

done <<< "$issue_lines"

if [[ "$WAIT_SECONDS" -eq 0 ]]; then
  echo "All Jules tasks started (not waiting for completion)."
  exit 0
fi

start_ts="$(date +%s)"
while :; do
  running="$(jobs -pr | wc -l | tr -d ' ')"
  if [[ "$running" -eq 0 ]]; then
    echo "All Jules tasks started."
    exit 0
  fi
  now_ts="$(date +%s)"
  elapsed="$((now_ts - start_ts))"
  if [[ "$elapsed" -ge "$WAIT_SECONDS" ]]; then
    echo "Timed out waiting for Jules tasks after ${WAIT_SECONDS}s (background jobs may still be running)."
    exit 0
  fi
  sleep 2
done
