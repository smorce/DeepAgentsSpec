#!/usr/bin/env bash
#
# scripts/validate_spec.sh
#
# Spec Quality Checklist（requirements.md）に未チェックの項目が残っていないか検査し、
# harness/AI-Agent-progress.txt に結果を追記するスクリプト。
#
# 使い方:
#   # 全てのフィーチャのチェックリストをまとめて検査
#   ./scripts/validate_spec.sh
#
#   # 特定のチェックリストだけ検査
#   ./scripts/validate_spec.sh \
#     plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
#
# 結果:
#   - PASSED の場合: 終了コード 0、progress ファイルに PASSED ログを追記
#   - FAILED の場合: 終了コード 1、progress ファイルに FAILED ログ + 未達項目一覧を追記
#

set -euo pipefail

# タイムスタンプ（UTC, "YYYY-MM-DD HH:MMZ" 形式）
timestamp() {
  date -u +"%Y-%m-%d %H:%MZ"
}

# リポジトリルートの決定
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  REPO_ROOT="$git_root"
else
  # git が使えない環境では、このスクリプトの 1 つ上をルートとして扱う
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

PROGRESS_FILE="$REPO_ROOT/harness/AI-Agent-progress.txt"

# 対象となるチェックリストファイルを集める
CHECKLIST_FILES=()

if [ "$#" -gt 0 ]; then
  # 引数で明示的に指定されたパスを使う
  for arg in "$@"; do
    # 相対パスの場合もあるので、そのまま受け取り、後で存在チェックする
    CHECKLIST_FILES+=("$arg")
  done
else
  # plans 以下の「features/*/checklists/requirements.md」を全部拾う
  # 例: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
  while IFS= read -r path; do
    CHECKLIST_FILES+=("$path")
  done < <(find "$REPO_ROOT/plans" -type f -path "*/features/*/checklists/requirements.md" | sort || true)
fi

if [ "${#CHECKLIST_FILES[@]}" -eq 0 ]; then
  # 対象ファイルが 1 つも見つからない場合は FAILED として扱う
  msg="[$(timestamp)] spec quality check: FAILED (no checklist files found)"
  echo "$msg" | tee -a "$PROGRESS_FILE" >&2
  exit 1
fi

overall_status=0

for file in "${CHECKLIST_FILES[@]}"; do
  # 絶対パス / 相対パスの両方を許容する
  if [[ "$file" != /* ]]; then
    # 相対パスなら REPO_ROOT からの相対とみなして解決する
    file="$REPO_ROOT/$file"
  fi

  if [ ! -f "$file" ]; then
    {
      echo "[$(timestamp)] spec quality check: FAILED"
      echo "target: $file"
      echo "incomplete items:"
      echo "  - checklist file not found"
    } | tee -a "$PROGRESS_FILE" >&2
    overall_status=1
    continue
  fi

  # リポジトリルートからの相対パス（ログを読みやすくするため）
  rel_path="${file#$REPO_ROOT/}"

  # 未チェックのチェックボックス行を grep する
  # パターン: 先頭近くに "- [ ]" がある行
  # 例: "- [ ] No implementation details ..."
  issues="$(grep -nE '^[[:space:]]*-[[:space:]]*\[ \]' "$file" || true)"

  if [ -z "$issues" ]; then
    # 未チェックなし → PASSED
    {
      echo "[$(timestamp)] spec quality check: PASSED"
      echo "target: $rel_path"
    } | tee -a "$PROGRESS_FILE"
  else
    # 未チェックあり → FAILED
    overall_status=1
    {
      echo "[$(timestamp)] spec quality check: FAILED"
      echo "target: $rel_path"
      echo "incomplete items:"
      # grep の出力形式は "行番号:行内容" なので、行番号と内容に分解して箇条書きにする
      while IFS= read -r line; do
        # "123: - [ ] ..." → num="123", text=" - [ ] ..."
        num="${line%%:*}"
        text="${line#*:}"
        # 先頭の空白をトリム
        text="${text#"${text%%[![:space:]]*}"}"
        echo "  - line ${num}: ${text}"
      done <<< "$issues"
    } | tee -a "$PROGRESS_FILE"
  fi
done

exit "$overall_status"