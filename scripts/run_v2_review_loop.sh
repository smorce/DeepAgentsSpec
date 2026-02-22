#!/usr/bin/env bash
# V2 レビューループ: Codex CLI の非対話モードを for ループで回し、
# レビューステータスが complete になるまで繰り返す。
# 各セッションは新しい Codex プロセスで実行される（コンテキストリセット）。
#
# 使い方:
#   bash scripts/run_v2_review_loop.sh <review_dir>
#   例: bash scripts/run_v2_review_loop.sh harness/agent_radar/reviews/REV-EXP-084

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAX_SESSIONS=5

REVIEW_DIR="${1:?Usage: run_v2_review_loop.sh <review_dir>}"

if [[ ! "$REVIEW_DIR" = /* ]]; then
  REVIEW_DIR="$REPO_ROOT/$REVIEW_DIR"
fi

PLAN_FILE="$REVIEW_DIR/plan.md"
STATUS_FILE="$REVIEW_DIR/status.json"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "ERROR: plan.md not found in $REVIEW_DIR" >&2
  exit 1
fi

if [[ ! -f "$STATUS_FILE" ]]; then
  echo "ERROR: status.json not found in $REVIEW_DIR" >&2
  exit 1
fi

get_status() {
  python3 -c "import json,sys; d=json.load(open('$STATUS_FILE')); print(d.get('status','unknown'))"
}

current_status=$(get_status)
if [[ "$current_status" == "complete" ]]; then
  echo "Review already complete."
  exit 0
fi

if [[ "$current_status" == "rejected" ]]; then
  echo "Review was rejected."
  exit 1
fi

for session_num in $(seq 1 $MAX_SESSIONS); do
  echo "=== Review Session $session_num / $MAX_SESSIONS ==="

  current_status=$(get_status)
  if [[ "$current_status" == "complete" ]]; then
    echo "Review approved at session $session_num."
    exit 0
  fi

  if [[ "$current_status" == "rejected" ]]; then
    echo "Review rejected at session $session_num."
    exit 1
  fi

  # 過去のレビューメモを集約
  PAST_REVIEWS=""
  for rf in "$REVIEW_DIR"/review-session-*.md; do
    if [[ -f "$rf" ]]; then
      PAST_REVIEWS="$PAST_REVIEWS
$(cat "$rf")"
    fi
  done

  PLAN_CONTENT=$(cat "$PLAN_FILE")
  IDEA_TITLE=$(python3 -c "import json; d=json.load(open('$STATUS_FILE')); print(d.get('idea_title',''))" 2>/dev/null || echo "")

  # レビューエージェントプロンプト
  REVIEW_PROMPT="あなたはハーネスエンジニアリングのレビュー担当エージェントです。

## レビュー対象
${PLAN_CONTENT}

## 評価観点
以下の5軸で1-5のスコアを付けてください。
1. harness_relevance（ハーネス関連性）: ハーネスエンジニアリングの改良に直結するか
2. feasibility（実現可能性）: 現在のコードベースで実装可能か
3. risk（リスク）: 破壊的変更や副作用のリスクの低さ（5=低リスク）
4. roi（ROI）: 投入工数に対する改善効果
5. sor_consistency（SoR整合性）: 既存のSoR原則と矛盾しないか

## 過去のレビューメモ
${PAST_REVIEWS:-（初回レビュー）}

## 完了条件
- 全スコアが3以上 かつ 平均3.5以上で approve
- 改善不可能な問題がある場合は reject

## 出力形式（JSON）
{\"scores\":{\"harness_relevance\":0,\"feasibility\":0,\"risk\":0,\"roi\":0,\"sor_consistency\":0},\"verdict\":\"approve|revise|reject\",\"comments\":\"\",\"focus_areas\":[\"\"],\"strengths\":[\"\"]}

JSONのみ出力してください。"

  # Codex CLI 非対話モードでレビュー実行
  SESSION_FILE="$REVIEW_DIR/review-session-$(printf '%03d' $session_num).md"
  REVIEW_OUTPUT=$(codex exec "$REVIEW_PROMPT" 2>/dev/null || echo '{"verdict":"revise","comments":"codex exec failed","scores":{}}')

  # レビュー結果を保存
  echo "# Review Session $session_num" > "$SESSION_FILE"
  echo "" >> "$SESSION_FILE"
  echo "- Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$SESSION_FILE"
  echo "" >> "$SESSION_FILE"
  echo '```json' >> "$SESSION_FILE"
  echo "$REVIEW_OUTPUT" >> "$SESSION_FILE"
  echo '```' >> "$SESSION_FILE"

  # 判定チェック
  VERDICT=$(echo "$REVIEW_OUTPUT" | python3 -c "
import json,sys
try:
    d=json.loads(sys.stdin.read())
    print(d.get('verdict','unknown'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

  PASSED=$(echo "$REVIEW_OUTPUT" | python3 -c "
import json,sys
try:
    d=json.loads(sys.stdin.read())
    scores=d.get('scores',{})
    criteria=['harness_relevance','feasibility','risk','roi','sor_consistency']
    vals=[scores.get(c,0) for c in criteria]
    all_min=all(v>=3 for v in vals)
    avg=sum(vals)/len(vals) if vals else 0
    approved=d.get('verdict')=='approve' and all_min and avg>=3.5
    print('true' if approved else 'false')
except:
    print('false')
" 2>/dev/null || echo "false")

  # status.json 更新
  python3 -c "
import json
with open('$STATUS_FILE') as f:
    status=json.load(f)
status.setdefault('sessions',[]).append({
    'session_id':'session-$(printf '%03d' $session_num)',
    'verdict':'$VERDICT',
})
if '$PASSED'=='true':
    status['status']='complete'
elif '$VERDICT'=='reject':
    status['status']='rejected'
with open('$STATUS_FILE','w') as f:
    json.dump(status,f,ensure_ascii=False,indent=2)
    f.write('\n')
"

  if [[ "$PASSED" == "true" ]]; then
    echo "Review APPROVED at session $session_num."
    exit 0
  fi

  if [[ "$VERDICT" == "reject" ]]; then
    echo "Review REJECTED at session $session_num."
    exit 1
  fi

  # 修正エージェントで計画を改善
  echo "Verdict: $VERDICT — running fix agent..."
  FIX_PROMPT="あなたはハーネスエンジニアリングの計画修正エージェントです。
以下のレビュー指摘に基づいて、実行計画を修正してください。

## 現在の計画
${PLAN_CONTENT}

## レビュー指摘
${REVIEW_OUTPUT}

修正後の計画をMarkdown形式で出力してください。"

  FIXED_PLAN=$(codex exec "$FIX_PROMPT" 2>/dev/null || echo "$PLAN_CONTENT")
  echo "$FIXED_PLAN" > "$PLAN_FILE"
  PLAN_CONTENT="$FIXED_PLAN"

  echo "Plan updated. Moving to next session."
  echo ""
done

echo "Max sessions ($MAX_SESSIONS) reached without approval."

# needs_human_review に設定
python3 -c "
import json
with open('$STATUS_FILE') as f:
    status=json.load(f)
status['status']='needs_human_review'
with open('$STATUS_FILE','w') as f:
    json.dump(status,f,ensure_ascii=False,indent=2)
    f.write('\n')
"

exit 2
