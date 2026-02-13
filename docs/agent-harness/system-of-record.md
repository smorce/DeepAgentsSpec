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
- 実験バックログ: `harness/agent_radar/experiment_backlog.json`
- 実装アーティファクト: `harness/agent_radar/implemented/`
- ランタイム状態スキーマ: `harness/agent_radar/runtime_state_schema.json`
- 自律成長ログ: `docs/agent-harness/autonomous-growth.md`

## データ更新責務

- 収集器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update`): ソース取得、差分検出、SoR更新
- 検証器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`): 境界逸脱や構造崩れの検出
- バックログ同期器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`): `new-items.json` を実験バックログへ自動反映
- 実装器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement`): バックログ項目を実装アーティファクト・監視・黄金律へ反映
- ガーデナー (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`): 文書劣化（TODO/未確定記法）の検出
- 制御器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`): 収集から実装までを自律実行する入口

## 境界

- 許可ソースは6ブログのみ。
- 許可外ドメインのリンクは `RadarItem` として保存しない。
- 収集失敗は許容するが、失敗イベントは進捗ログへ残す。
