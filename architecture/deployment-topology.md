# デプロイメントトポロジー

## ローカル実行

- 収集/検証/実装/ガーデニングはローカルで実行可能。
- 主要コマンド:
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

## CI実行（推奨）

日次またはPR時に以下順で実行します。

1. Source update
2. Boundary validation
3. Experiment backlog sync
4. Autonomous implementation
5. Doc gardening

失敗時はマージ不可とし、境界逸脱と文書劣化を早期に止めます。

## 永続化配置

- Hot state: `harness/agent_radar/state.json`
- Latest snapshot: `harness/agent_radar/snapshot-latest.json`
- Diff output: `harness/agent_radar/new-items.json`
- Report: `docs/reports/source-radar/*.md`

## 将来拡張

- MCP経由の外部検証結果（例: UI検証）を state schema に連結
- GitHub Actions 以外の外部 Scheduler 連携を追加
