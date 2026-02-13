# Agent Harness Quickstart

## 前提

- ブランチ: `feat/agent-harness-sor-radar`
- 実行環境: Python 3.11+ / `uv` 利用可能
- 実行ディレクトリ: リポジトリルート

## 1. 最短実行（推奨）

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2
```

この1コマンドで、収集→検証→バックログ化→実装→再検証→ガーデニング→監視評価まで実行します。

## 2. ステップ別に実行したい場合

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update --collector auto
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden
```

## 3. 実行後に確認するファイル

- 差分/収集結果:
  - `harness/agent_radar/new-items.json`
  - `harness/agent_radar/snapshot-latest.json`
- 実装結果:
  - `harness/agent_radar/experiment_backlog.json`
  - `harness/agent_radar/mutations/index.json`
- 監視:
  - `harness/agent_radar/metrics/latest.json`
  - `harness/agent_radar/monitoring_results.json`
- 自己修復:
  - `harness/agent_radar/self_heal_log.json`

## 4. 典型トラブル

1. `validate` が失敗する  
`autogrow` なら自己修復して再試行します。最終的に失敗する場合は `self_heal_log.json` の `actions` を確認してください。

2. Codex収集が不安定  
`--collector auto` を使うと native にフォールバックします。厳格運用時のみ `--collector codex` を使ってください。

3. OneDrive のリンクモード問題  
必ず `--link-mode=copy` を維持してください。

## 5. 日次運用

- GitHub Actions: `.github/workflows/agent-radar-daily.yml`
- 日次ジョブが SoR 更新差分を自動コミットします。
