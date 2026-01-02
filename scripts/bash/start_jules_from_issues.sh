#!/usr/bin/env bash
set -euo pipefail

# Usage: ./start_jules_from_issues.sh [limit]
LIMIT="${1:-2}"

# LIMIT が整数か確認
if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "Error: limit must be a non-negative integer (got: $LIMIT)" >&2
  exit 1
fi

# 自分にアサインされた open Issue を最大 LIMIT 件取得
issues=$(gh issue list \
  --assignee @me \
  --state open \
  --limit "$LIMIT" \
  --json number,title)

count=$(echo "$issues" | jq 'length')
if [ "$count" -eq 0 ]; then
  echo "No open issues assigned to me"
  exit 0
fi

echo "Starting $count Jules tasks in parallel..."

while IFS= read -r issue; do
  number=$(echo "$issue" | jq -r '.number')
  title=$(echo "$issue" | jq -r '.title')

  # Issue 本文を取得
  body=$(gh issue view "$number" --json body -q '.body')

  # Jules に渡すプロンプトを組み立て
  prompt=$(cat <<EOF
You are working on the following GitHub Issue.

Issue Number: #$number
Title:
$title

Description:
$body

Please implement this task.
EOF
)

  echo "→ Starting Jules task for Issue #$number"

  # 公式の想定どおり、stdin でプロンプトを渡す
  printf '%s\n' "$prompt" | jules remote new --repo . &

done < <(echo "$issues" | jq -c '.[]')

wait
echo "All Jules tasks started."