# Agent Harness Control Loop

## V1 ループ構造

1. Detect: 指定ブログの更新を検出する。
2. Verify: 許可境界と構造妥当性を検証する。
3. Curate: 差分を実験バックログへ自動起票する。
4. Implement: バックログ項目から実装アーティファクト・監視・黄金律を生成する。
5. Encode: 成果を黄金律へ昇格する。
6. Garden: 仕様・計画・運用文書の劣化を修復する。

## V2 ループ構造（自律的ハーネスエンジニアリング改良）

V1がタイトル/URL収集とテンプレ生成に留まるのに対し、V2は実際のコードベース改修まで行う。

1. Radar: 記事の本文をCodex CLIで読み、ハーネス改善アイデアを抽出する。
2. Analyze: アイデアをコードベースと突き合わせ、ギャップ分析（現状→理想→差分）を行う。
3. Review Loop: Codex CLI非対話モードの多段レビュー（最大5セッション、5軸評価）を行う。
4. Execute: レビュー通過した計画に基づき、コードベースを改修する。
5. Validate: V1のvalidateを実行し、改修後の整合性を検証する。
6. Garden: V1のgardenを実行し、文書の劣化を修復する。

詳細設計: `docs/agent-harness/harness-v2-design.md`

## 実行コマンド

```bash
# V1 のみ
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2

# V1 + V2 統合（推奨）
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow-v2 --collector auto --self-heal-max-retries 2

# V2 パイプライン単独
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode v2-pipeline
```

Codex収集を強制したい場合は `--collector codex` を指定する。
自己修復の試行回数は `--self-heal-max-retries` で制御する。

## 失敗時ポリシー

### V1 ステップ

- update 失敗: `native` 収集にフォールバックして再試行する。
- validate 失敗: 境界逸脱データをトリムして再検証する。
- implement/backlog 失敗: バックログ JSON 構造を自己修復して再試行する。
- garden 失敗: placeholder 行を自動置換して再試行する。

### V2 ステップ

- radar 失敗（Codex exec失敗）: 該当記事をスキップし、次の記事へ進む。
- analyze 失敗: 該当アイデアをスキップし、エラーを progress log へ記録する。
- review 失敗（Codex exec失敗）: 該当セッションをスキップし、次のセッションへ進む。
- execute 失敗: 変更は部分適用され `result.json` に `partial` ステータスで記録する。ロールバックスクリプトが利用可能。
- 全ステップ共通: 失敗イベントは `harness/AI-Agent-progress.txt` に記録する。

修復履歴: `harness/agent_radar/self_heal_log.json` に保存する。

## 監視対象

### V1 メトリクス

- 新規記事数 (`radar.new_item_count`)
- 実装完了件数 (`radar.implemented_total`)
- 収集成功率（source 単位）
- 許可外リンク検出件数
- ドキュメント劣化件数
- 自己修復実行回数 (`autogrow.self_heal_actions`)
- 監視評価結果 (`harness/agent_radar/monitoring_results.json`)

### V2 メトリクス

- 抽出アイデア数 (`v2.ideas_extracted`)
- ギャップ分析実行数 (`v2.analyses_completed`)
- 採用アイデア数 (`v2.ideas_adopted`)
- 不採用アイデア数 (`v2.ideas_rejected`)
- レビュー通過数 (`v2.reviews_approved`)
- 実行成功数 (`v2.executions_completed`)
- レビュー平均セッション数 (`v2.avg_review_sessions`)
