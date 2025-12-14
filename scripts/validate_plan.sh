#!/usr/bin/env bash
#
# scripts/validate_plan.sh
#
# impl-plan + 設計成果物に対する Plan 品質チェックリスト（plan.md）を検証し、
# harness/AI-Agent-progress.txt に結果を追記するスクリプト。
#
# 使い方:
#   # 全てのフィーチャの Plan チェックリストをまとめて検査
#   ./scripts/validate_plan.sh
#
#   # 特定のチェックリストだけ検査
#   ./scripts/validate_plan.sh \
#     plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/plan.md
#
# 結果:
#   - PASSED の場合: 終了コード 0、progress ファイルに PASSED ログを追記
#   - FAILED の場合: 終了コード 1、progress ファイルに FAILED ログ + 未達項目一覧を追記
#

### スクリプトの仕様

# * 対象:

#   * 引数なし: `plans/**/features/*/checklists/PlanQualityGate.md` を全て検査
#   * 引数あり: 引数で指定された `PlanQualityGate.md` のみ検査

# * 振る舞い:

#   * 各 `PlanQualityGate.md` 内の未チェック項目（`- [ ]`）を検出
#   * 1 つでも未チェック項目があれば **FAILED**
#   * すべて `- [x]` なら **PASSED**

# * ログ:

#   * 結果を `harness/AI-Agent-progress.txt` に追記
#   * 例:

#     * PASSED:

#       ```text
#       [2025-10-01 13:05Z] plan quality check: PASSED
#       target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/PlanQualityGate.md
#       ```

#     * FAILED:

#       ```text
#       [2025-10-01 13:05Z] plan quality check: FAILED
#       target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/PlanQualityGate.md
#       incomplete items:
#         - line 23: - [ ] Technical Context has no NEEDS CLARIFICATION markers
#         - line 41: - [ ] data-model.md exists and matches the spec
#       ```

# * 終了コード:

#   * `0` — すべての Plan チェックリストが PASS
#   * `1` — 少なくとも 1 つ FAIL またはチェックリストファイル未発見

## 運用フローへの組み込みイメージ

# フィーチャ 1 件あたり：

# 1. `specify → clarify → scripts/validate_spec.sh` が PASS
# 2. `/speckit.plan` で `impl-plan.md` + `research.md` + `data-model.md` + `contracts/` + `quickstart.md` を生成・更新
# 3. AIエージェントのレビューで `checklists/PlanQualityGate.md` を埋める（`- [x]` にする）
# 4. `scripts/validate_plan.sh [PlanQualityGate.md]` を回す
# 5. Plan 品質ゲートが PASS したら `/speckit.tasks` にハンドオフ

# こうしておくと、
# * **仕様の穴**は `validate_spec.sh`
# * **設計・Plan の穴**は `validate_plan.sh`

set -euo pipefail

timestamp() {
  date -u +"%Y-%m-%d %H:%MZ"
}

# リポジトリルート決定
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  REPO_ROOT="$git_root"
else
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

PROGRESS_FILE="$REPO_ROOT/harness/AI-Agent-progress.txt"

PLAN_CHECKLIST_FILES=()

if [ "$#" -gt 0 ]; then
  # 引数で明示指定されたパスを使う
  for arg in "$@"; do
    PLAN_CHECKLIST_FILES+=("$arg")
  done
else
  # plans 以下の「features/*/checklists/PlanQualityGate.md」を全部拾う
  while IFS= read -r path; do
    PLAN_CHECKLIST_FILES+=("$path")
  done < <(find "$REPO_ROOT/plans" -type f -path "*/features/*/checklists/PlanQualityGate.md" | sort || true)
fi

if [ "${#PLAN_CHECKLIST_FILES[@]}" -eq 0 ]; then
  msg="[$(timestamp)] plan quality check: FAILED (no plan checklist files found)"
  echo "$msg" | tee -a "$PROGRESS_FILE" >&2
  exit 1
fi

overall_status=0

for file in "${PLAN_CHECKLIST_FILES[@]}"; do
  # 絶対パス / 相対パス両対応
  if [[ "$file" != /* ]]; then
    file="$REPO_ROOT/$file"
  fi

  if [ ! -f "$file" ]; then
    {
      echo "[$(timestamp)] plan quality check: FAILED"
      echo "target: $file"
      echo "incomplete items:"
      echo "  - checklist file not found"
    } | tee -a "$PROGRESS_FILE" >&2
    overall_status=1
    continue
  fi

  rel_path="${file#$REPO_ROOT/}"

  # 未チェックのチェックボックス行を grep
  issues="$(grep -nE '^[[:space:]]*-[[:space:]]*\[ \]' "$file" || true)"

  if [ -z "$issues" ]; then
    {
      echo "[$(timestamp)] plan quality check: PASSED"
      echo "target: $rel_path"
    } | tee -a "$PROGRESS_FILE"
  else
    overall_status=1
    {
      echo "[$(timestamp)] plan quality check: FAILED"
      echo "target: $rel_path"
      echo "incomplete items:"
      while IFS= read -r line; do
        num="${line%%:*}"
        text="${line#*:}"
        text="${text#"${text%%[![:space:]]*}"}"
        echo "  - line ${num}: ${text}"
      done <<< "$issues"
    } | tee -a "$PROGRESS_FILE"
  fi
done

exit "$overall_status"