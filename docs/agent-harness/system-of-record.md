# Agent Harness System of Record

## 目的

このドキュメントは、AIエージェントハーネス進化プロジェクトの唯一の運用参照を定義します。  
人間の一時的な会話や外部メモではなく、リポジトリ内アーティファクトだけで継続改善を成立させることが目的です。

## SoR の配置

- ソース定義: `harness/agent_radar/official_sources.json`
- 収集状態: `harness/agent_radar/state.json`
- 最新スナップショット: `harness/agent_radar/snapshot-latest.json`
- 新規差分: `harness/agent_radar/new-items.json`
- 黄金律: `harness/agent_radar/golden_rules.json`
- 監視ターゲット: `harness/agent_radar/monitoring_targets.json`
- 監視評価結果: `harness/agent_radar/monitoring_results.json`
- 実験バックログ: `harness/agent_radar/experiment_backlog.json`
- 実装アーティファクト: `harness/agent_radar/implemented/`
- 自己改変モジュール: `harness/agent_radar/mutations/`
- 自己改変インデックス: `harness/agent_radar/mutations/index.json`
- 実行メトリクス: `harness/agent_radar/metrics/latest.json`
- 実行メトリクス履歴: `harness/agent_radar/metrics/history.jsonl`
- 自己修復ログ: `harness/agent_radar/self_heal_log.json`
- ランタイム状態スキーマ: `harness/agent_radar/runtime_state_schema.json`
- 自律成長ログ: `docs/agent-harness/autonomous-growth.md`
- Codex収集監査ログ: `docs/reports/source-radar/codex-exec/`

## データ更新責務

- 収集器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update --collector auto`): ソース取得、差分検出、SoR更新
  - `--collector auto`: Codex収集を試行し、失敗時は native 収集へフォールバック
  - `--collector codex`: Codex収集を強制（失敗時はエラー終了）
  - `--collector native`: Python実装のみで収集
- 検証器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`): 境界逸脱や構造崩れの検出
- バックログ同期器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`): `new-items.json` を実験バックログへ自動反映
- 実装器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement`): バックログ項目を実装アーティファクト・監視・黄金律へ反映
- 監視評価器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow` 内): 実行メトリクスを生成し `monitoring_targets.json` を評価
- 自己修復器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --self-heal-max-retries 2`): 失敗時に原因カテゴリ別の修復を実行し再試行
- ガーデナー (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`): 文書劣化（TODO/未確定記法）の検出
- 制御器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2`): 収集から実装までを自律実行する入口

## 境界

- 許可ソースは6ブログのみ。
- 許可外ドメインのリンクは `RadarItem` として保存しない。
- `latest_url` と `evidence_url` は source ごとの許可プレフィックスで検証する。
- 収集失敗は許容するが、失敗イベントは進捗ログへ残す。
