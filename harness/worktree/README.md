# Worktree Harness

`harness/worktree/worktree_ops.py` は、タスクごとに隔離 worktree を作り、
「再現 -> 修正 -> 検証 -> 証跡生成」を1回で実行する実行器です。

## 目的

- タスク単位の隔離実行（`git worktree`）
- 実行ログの永続化（stdout/stderr）
- メトリクス・スクリーンショットの証跡化
- 失敗時の再現スクリプト（`replay.sh`）生成

## 実行コマンド

```bash
uv run --no-project --link-mode=copy python harness/worktree/worktree_ops.py \
  --task-id TASK-001 \
  --repro-cmd "bash scripts/run_all_unit_tests.sh" \
  --repro-expected-exit 1 \
  --fix-prompt "Fix failing tests for TASK-001. Keep changes minimal and update tests." \
  --verify-cmd "bash scripts/run_all_unit_tests.sh" \
  --verify-expected-exit 0 \
  --screenshot-url "http://localhost:8080" \
  --metrics-file harness/agent_radar/metrics/latest.json
```

## 生成物

1回の実行で `harness/worktree/runs/<RUN_ID>/` が作成されます。

- `run.json`: 実行マニフェスト
- `logs/*.log`: フェーズごとの stdout/stderr
- `artifacts/git-diff.patch`: 差分パッチ
- `artifacts/replay.sh`: 再現用スクリプト
- `metrics/run-metrics.json`: 実行メトリクス
- `evidence/summary.md`: 証跡サマリ
- `screenshots/*.png`: スクリーンショット（指定時）

## 運用メモ

- `--fix-prompt` を使うと `codex exec` で修正フェーズを自動実行できます。
- 失敗時は worktree を保持し、成功時はデフォルトで自動削除します。
- 常時保持したい場合は `--keep-worktree` を指定します。
