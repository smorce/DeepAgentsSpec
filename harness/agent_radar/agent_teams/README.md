# Agent Teams Template (Harness Flow)

このディレクトリは、`Agent Teams相当` をハーネス運用へ組み込むためのテンプレート一式です。

## 目的

- 単一成功パターンへの収斂を防ぐ
- `improvement_family`（schema上は `strategy_family`）ごとの探索を並列に評価する
- `worktree` 隔離で再現・修正・検証・証跡生成を機械的に担保する

## 構成

- `input_schema.json`  
  Agent Teams実行入力のJSONスキーマ
- `context_bundle.example.json`  
  入力の最小サンプル（family 2本）
- `prompts/generator.md`  
  teammate用（family固定）
- `prompts/evaluator.md`  
  teammate評価用（family固有基準）
- `prompts/lead.md`  
  最終統合用（Lead専用）

## 運用手順（推奨）

1. `context_bundle.example.json` を複製し、対象タスク用に編集する。
2. `shared_context.forbidden_context` に「見てはいけない情報」を明示する。
3. teammateごとに `strategy_family`（改善軸）を固定する。
4. teammate実行は `harness/worktree/worktree_ops.py` で隔離する。
5. Leadが統合比較して最終選定する。

## teammate実行の最小例

```bash
uv run --no-project --link-mode=copy python harness/worktree/worktree_ops.py \
  --task-id TEAM-A-RUN-001 \
  --repro-cmd "true" \
  --repro-expected-exit 0 \
  --fix-prompt-file harness/agent_radar/executions/EXEC-EXP-001/fix-prompt.txt \
  --verify-cmd "uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate && uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden" \
  --verify-expected-exit 0 \
  --metrics-file harness/agent_radar/metrics/latest.json \
  --keep-worktree
```

## 設計原則

- **No fallback concealment**: 失敗は隠蔽せず観測する
- **Family isolation**: teammateは割り当てfamily外へ逸脱しない
- **Lead-only final selection**: 最終比較はLeadのみ
- **SoR first**: 実行証跡はリポジトリ内に残す
- **Harness growth first**: 目的はハーネス自体の自律成長
