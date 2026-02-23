# デプロイメントトポロジー

## ローカル実行

- V2統合パイプライン（記事分析→ギャップ分析→レビュー→worktree実行→再検証→ガーデニング）はローカルで実行可能（Codex CLI が必要）。

### 実行コマンド

  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-radar`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-analyze`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --collector auto --self-heal-max-retries 2`
  - `bash scripts/run_v2_review_loop.sh <review_dir>`

## CI実行（推奨）

日次またはPR時に以下順で実行します。

### V2 ステップ（日次）

1. Article analysis (Radar)
2. Gap analysis
3. Review loop
4. Worktree execution (reproduce -> fix -> verify -> evidence)
5. Post-execution validate + garden
6. Monitoring publish

失敗時はマージ不可とし、境界逸脱と文書劣化を早期に止めます。

## 永続化配置

### V2

- Ideas: `harness/agent_radar/ideas/IDEA-*.json`
- Rejected ideas: `harness/agent_radar/ideas/rejected/IDEA-R*.json`
- Gap analysis: `harness/agent_radar/analysis/GAP-*.json`
- Reviews: `harness/agent_radar/reviews/REV-*/`
- Executions: `harness/agent_radar/executions/EXEC-*/`
- Knowledge base: `harness/agent_radar/knowledge_base.json`
- Worktree evidence: `harness/worktree/runs/`

## 前提条件

- Python 3.11+ / `uv` 利用可能
- `codex` CLI が PATH 上に存在すること（Codex CLI のインストールが必要）

## 将来拡張

- MCP経由の外部検証結果（例: UI検証）を state schema に連結
- GitHub Actions 以外の外部 Scheduler 連携を追加
- V2 レビューループのセッション数やスコア閾値のチューニング
- V2 Executor の変更スコープ制限（影響範囲の上限設定）
