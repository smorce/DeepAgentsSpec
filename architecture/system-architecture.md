# システムアーキテクチャ

## 目的

このリポジトリは、AIエージェントによる長期自律開発を維持するためのハーネスを、リポジトリ内だけで継続進化させることを目的とします。
中心思想は「コードを書く前に、環境・意図・フィードバックループを設計する」です。

## システム構成

### V1 レイヤー（SoR周りの自律改善）

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

### V2 レイヤー（自律的ハーネスエンジニアリング改良）

5. Article Analysis Layer
   - 公式ブログの記事本文をCodex CLIで読み、ハーネスエンジニアリングに適用可能なアイデアを抽出する。
   - 補足として Zenn/Qiita/note の解説記事も参照する。
   - SoR: `harness/agent_radar/ideas/`, `harness/agent_radar/knowledge_base.json`

6. Gap Analysis Layer
   - 抽出したアイデアを現在のコードベースと突き合わせ、現状→理想→差分のギャップ分析を行う。
   - 不採用アイデアは理由付きで永続化する。
   - SoR: `harness/agent_radar/analysis/`, `harness/agent_radar/ideas/rejected/`

7. Review Loop Layer
   - 採用アイデアの実行計画を Codex CLI 非対話モードのマルチセッションで多段レビューする。
   - 5軸評価（ハーネス関連性/実現可能性/リスク/ROI/SoR整合性）で判定する。
   - SoR: `harness/agent_radar/reviews/`

8. Execution Layer
   - レビュー通過した計画に基づき、実際のコードベース改修を行う。
   - ディレクトリ構造変更はマークダウンでSoR化→スクリプト生成→実行の三段階。
   - SoR: `harness/agent_radar/executions/`
   - 設計書: `docs/agent-harness/harness-v2-design.md`

## データフロー

### V1 フロー

- 収集器が公式ブログ更新を検知し `snapshot-latest.json` を更新
- 差分検知器が `new-items.json` を生成
- バリデータが許可外URL混入や構造破損を拒否
- 実装器が `experiment_backlog.json` から実装アーティファクトと監視ターゲットを生成
- ガーデナーがプレースホルダー残存と SoR 同期ズレ（古い文書）を検知

### V2 フロー

- Radar が記事本文を分析し `ideas/IDEA-*.json` へアイデアを保存
- Analyzer がギャップ分析を行い `analysis/GAP-*.json` へ結果を保存（不採用は `ideas/rejected/` へ）
- Review Loop が計画を多段評価し `reviews/REV-*/` へセッション記録を蓄積
- Executor が改修を実行し `executions/EXEC-*/` へ結果とロールバックスクリプトを保存
- V1 の validate/garden で改修後の整合性を検証

### 統合フロー

- `autogrow-v2` は V1 autogrow 完了後に V2 pipeline を続けて実行する
- 人間判断が必要なものだけをエスカレーション

## 設計原則

- Source boundary first: 指定された公式URL以外を学習ソース化しない（V2では補足としてZenn/Qiita/noteも参照）。
- Progressive disclosure: AGENTS.mdは目次化し、詳細は docs/plans へ分離。
- Mechanical enforcement: ルールは文書化だけでなくスクリプトで検証する。
- State externalization: 長文状態は会話に埋めず、参照トークン化する。
- Rejected idea preservation: 不採用アイデアも理由付きで永続化し、将来の再検討に備える。
- Multi-session review: 計画は毎回コンテキストをリセットした独立セッションで複数回レビューする。
