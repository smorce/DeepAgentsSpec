# デプロイメントトポロジー

## ローカル実行

- 収集/検証/実装/ガーデニングはローカルで実行可能。
- V2パイプライン（記事分析→ギャップ分析→レビュー→実行）もローカルで実行可能（Codex CLI が必要）。

### V1 コマンド

  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

### V2 コマンド

  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-radar`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-analyze`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-pipeline`
  - `bash scripts/run_v2_review_loop.sh <review_dir>`

### 統合コマンド

  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow-v2 --collector auto --self-heal-max-retries 2`

## CI実行（推奨）

日次またはPR時に以下順で実行します。

### V1 ステップ

1. Source update
2. Boundary validation
3. Experiment backlog sync
4. Autonomous implementation
5. Doc gardening

### V2 ステップ（日次）

6. Article analysis (Radar)
7. Gap analysis
8. Review loop
9. Execution
10. Post-execution validate + garden

失敗時はマージ不可とし、境界逸脱と文書劣化を早期に止めます。

## 永続化配置

### V1

- Hot state: `harness/agent_radar/state.json`
- Latest snapshot: `harness/agent_radar/snapshot-latest.json`
- Diff output: `harness/agent_radar/new-items.json`
- Report: `docs/reports/source-radar/*.md`

### V2

- Ideas: `harness/agent_radar/ideas/IDEA-*.json`
- Rejected ideas: `harness/agent_radar/ideas/rejected/IDEA-R*.json`
- Gap analysis: `harness/agent_radar/analysis/GAP-*.json`
- Reviews: `harness/agent_radar/reviews/REV-*/`
- Executions: `harness/agent_radar/executions/EXEC-*/`
- Knowledge base: `harness/agent_radar/knowledge_base.json`

## 前提条件

- V1: Python 3.11+ / `uv` 利用可能
- V2: 上記に加え `codex` CLI が PATH 上に存在すること（Codex CLI のインストールが必要）

## 将来拡張

- MCP経由の外部検証結果（例: UI検証）を state schema に連結
- GitHub Actions 以外の外部 Scheduler 連携を追加
- V2 レビューループのセッション数やスコア閾値のチューニング
- V2 Executor の変更スコープ制限（影響範囲の上限設定）
