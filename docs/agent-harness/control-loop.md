# Agent Harness Control Loop

## V2 統合ループ構造

1. Radar: 記事の本文をCodex CLIで読み、ハーネス改善アイデアを抽出する。
2. Analyze: アイデアをコードベースと突き合わせ、ギャップ分析（現状→理想→差分）を行う。
3. Review Loop: Codex CLI非対話モードの多段レビュー（最大5セッション、5軸評価）を行う。
4. Execute: レビュー通過した計画を、タスク単位の隔離worktreeで改修・検証・証跡化する。
5. Validate: 改修後の整合性を検証する。
6. Garden: 文書の鮮度を維持するために常に実行する。
7. Monitoring: 実行メトリクスと監視評価を更新する。

詳細設計: `docs/agent-harness/harness-v2-design.md`

## 実行コマンド

```bash
# V2 統合パイプライン（推奨）
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --collector auto --self-heal-max-retries 2
```

Codex収集を強制したい場合は `--collector codex` を指定する。
自己修復の試行回数は `--self-heal-max-retries` で制御する。

## 失敗時ポリシー

- radar 失敗（Codex exec失敗）: 該当記事をスキップし、次の記事へ進む。
- analyze 失敗: 該当アイデアをスキップし、エラーを progress log へ記録する。
- review 失敗（Codex exec失敗）: 該当セッションをスキップし、次のセッションへ進む。
- execute 失敗: worktree実行は失敗として記録し、証跡（stdout/stderr/run.json）を残す。
- 全ステップ共通: 失敗イベントは `harness/AI-Agent-progress.txt` に記録する。
- V1フォールバックは行わない（失敗は観測可能な形で残す）。

## 監視対象

- 抽出アイデア数 (`v2.ideas_extracted`)
- ギャップ分析実行数 (`v2.analyses_completed`)
- 採用アイデア数 (`v2.ideas_adopted`)
- 不採用アイデア数 (`v2.ideas_rejected`)
- レビュー通過数 (`v2.reviews_approved`)
- 実行成功数 (`v2.executions_completed`)
- レビュー平均セッション数 (`v2.avg_review_sessions`)
- 監視評価結果 (`harness/agent_radar/monitoring_results.json`)
