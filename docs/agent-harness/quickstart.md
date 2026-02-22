# Agent Harness Quickstart

## 前提

- ブランチ: 任意（対象変更を含む作業ブランチ）
- 実行環境: Python 3.11+ / `uv` 利用可能
- 実行ディレクトリ: リポジトリルート

## 1. 最短実行（推奨 — V1 + V2 統合）

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow-v2 --collector auto --self-heal-max-retries 2
```

V1（収集→検証→バックログ→実装→再検証→ガーデニング）に加え、V2（記事本文分析→ギャップ分析→レビューループ→コード改修）も実行します。

### V1 のみ実行したい場合

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2
```

### V2 のみ実行したい場合

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-pipeline
```

## 2. ステップ別に実行したい場合

### V1 ステップ

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update --collector auto
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden
```

### V2 ステップ

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-radar
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-analyze
```

### V2 レビューループ単独実行

```bash
bash scripts/run_v2_review_loop.sh harness/agent_radar/reviews/REV-EXP-084
```

## 3. 実行後に確認するファイル

### V1 成果物

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

### V2 成果物

- アイデア抽出: `harness/agent_radar/ideas/IDEA-*.json`
- 不採用アイデア: `harness/agent_radar/ideas/rejected/IDEA-R*.json`
- ギャップ分析: `harness/agent_radar/analysis/GAP-*.json`
- レビュー記録: `harness/agent_radar/reviews/REV-*/status.json`
- 実行結果: `harness/agent_radar/executions/EXEC-*/result.json`
- ナレッジベース: `harness/agent_radar/knowledge_base.json`

## 4. タスク隔離実行（reproduce -> fix -> evidence）

タスクごとに隔離 worktree を作成して、再現・修正・検証・証跡生成を一括実行できます。

```bash
uv run --no-project --link-mode=copy python harness/worktree/worktree_ops.py \
  --task-id TASK-001 \
  --repro-cmd "bash scripts/run_all_unit_tests.sh" \
  --repro-expected-exit 1 \
  --fix-prompt "Fix failing tests for TASK-001 with minimal changes." \
  --verify-cmd "bash scripts/run_all_unit_tests.sh" \
  --verify-expected-exit 0 \
  --screenshot-url "http://localhost:8080" \
  --metrics-file harness/agent_radar/metrics/latest.json
```

実行後の成果物は `harness/worktree/runs/<RUN_ID>/` に保存されます。
- `evidence/summary.md`
- `artifacts/replay.sh`
- `logs/*.log`
- `metrics/run-metrics.json`

## 5. 典型トラブル

1. `validate` が失敗する  
`autogrow` なら自己修復して再試行します。最終的に失敗する場合は `self_heal_log.json` の `actions` を確認してください。

2. Codex収集が不安定  
`--collector auto` を使うと native にフォールバックします。厳格運用時のみ `--collector codex` を使ってください。

3. OneDrive のリンクモード問題  
必ず `--link-mode=copy` を維持してください。

4. E2E の live API シナリオを回したい  
`RUN_LIVE_MINIRAG_E2E=1 bash scripts/run_all_e2e_tests.sh` を使ってください。  
未指定時は UI モックシナリオのみ実行されます。

## 6. 日次運用

- GitHub Actions: `.github/workflows/agent-radar-daily.yml`
- 日次ジョブが SoR 更新差分を自動コミットします。

## 7. PR品質ゲート

- GitHub Actions: `.github/workflows/quality-gates.yml`
- `pull_request` で以下を強制実行します。
  - `scripts/format_or_lint.sh`
  - `scripts/validate_spec.sh`
  - `scripts/validate_plan.sh`
  - `radar_ops.py --mode validate`
  - `scripts/garden_agent_docs.sh`
  - `scripts/run_all_unit_tests.sh`
  - `scripts/run_all_e2e_tests.sh`
