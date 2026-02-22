# システムアーキテクチャ

## 目的

このリポジトリは、AIエージェントによる長期自律開発を維持するためのハーネスを、リポジトリ内だけで継続進化させることを目的とします。  
中心思想は「コードを書く前に、環境・意図・フィードバックループを設計する」です。

## システム構成

1. Source Radar Layer
   - 指定6ブログのみを対象に更新を収集する。
   - SoR: `harness/agent_radar/official_sources.json`

2. Control Loop Layer
   - `update -> validate -> backlog -> implement -> validate -> garden` を制御し、境界逸脱と知見未整理を防ぐ。
   - 実行入口: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

3. State & Persistence Layer
   - 実行状態を会話から分離し、JSON/JSONLに永続化する。
   - スキーマ: `harness/agent_radar/runtime_state_schema.json`

4. Knowledge Layer
   - 仕様・計画・決定ログを repo 内で一貫管理する。
   - 主要文書: `plans/system/EPIC-SYS-001-harness-radar/`, `docs/agent-harness/`

## データフロー

- 収集器が公式ブログ更新を検知し `snapshot-latest.json` を更新
- 差分検知器が `new-items.json` を生成
- バリデータが許可外URL混入や構造破損を拒否
- 実装器が `experiment_backlog.json` から実装アーティファクトと監視ターゲットを生成
- ガーデナーがプレースホルダー残存と SoR 同期ズレ（古い文書）を検知
- 人間判断が必要なものだけをエスカレーション

## 設計原則

- Source boundary first: 指定された公式URL以外を学習ソース化しない。
- Progressive disclosure: AGENTS.mdは目次化し、詳細は docs/plans へ分離。
- Mechanical enforcement: ルールは文書化だけでなくスクリプトで検証する。
- State externalization: 長文状態は会話に埋めず、参照トークン化する。
