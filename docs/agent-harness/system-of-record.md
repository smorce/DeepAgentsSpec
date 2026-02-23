# Agent Harness System of Record

## 目的

このドキュメントは、AIエージェントハーネス進化プロジェクトの唯一の運用参照を定義します。  
人間の一時的な会話や外部メモではなく、リポジトリ内アーティファクトだけで継続改善を成立させることが目的です。

## 関連文書

- 解説書: `docs/agent-harness/guide.md`
- クイックスタート: `docs/agent-harness/quickstart.md`

## SoR の配置

- ソース定義: `harness/agent_radar/official_sources.json`
- 監視ターゲット: `harness/agent_radar/monitoring_targets.json`
- 監視評価結果: `harness/agent_radar/monitoring_results.json`
- 実行メトリクス: `harness/agent_radar/metrics/latest.json`
- 実行メトリクス履歴: `harness/agent_radar/metrics/history.jsonl`
- 自己修復ログ: `harness/agent_radar/self_heal_log.json`
- ランタイム状態スキーマ: `harness/agent_radar/runtime_state_schema.json`
- 自律成長ログ: `docs/agent-harness/autonomous-growth.md`
- Codex収集監査ログ: `docs/reports/source-radar/codex-exec/`
- タスク隔離実行器: `harness/worktree/worktree_ops.py`
- タスク実行証跡: `harness/worktree/runs/`

## データ更新責務

- 検証器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`): 境界逸脱や構造崩れの検出
- 監視評価器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline` 内): 実行メトリクスを生成し `monitoring_targets.json` を評価
- 自己修復器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --self-heal-max-retries 2`): 整合回復（監視鮮度・文書同期）を試行
- ガーデナー (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`): 文書劣化（TODO/未確定記法）と SoR同期ズレ（古い文書）の検出
- 制御器 (`uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --collector auto --self-heal-max-retries 2`): 収集から改修・再検証までを自律実行する入口

## V2 パイプライン SoR

V2では記事本文の分析、ギャップ分析、レビューループ、実際のコード改修を行う。

- アイデア抽出: `harness/agent_radar/ideas/IDEA-*.json`
- 不採用アイデア: `harness/agent_radar/ideas/rejected/IDEA-R*.json`
- ギャップ分析: `harness/agent_radar/analysis/GAP-*.json`
- レビュー記録: `harness/agent_radar/reviews/REV-*/`
  - `plan.md` — 実行計画（レビューを経て洗練されたもの）
  - `review-session-*.md` — 各セッションのレビュー結果
  - `status.json` — レビューステータス
- 実行記録: `harness/agent_radar/executions/EXEC-*/`
  - `dir-structure.md` — ディレクトリ構造変更のSoR
  - `change-script.py` — 変更スクリプト
  - `rollback-script.py` — ロールバックスクリプト
  - `result.json` — 実行結果
- ナレッジベース: `harness/agent_radar/knowledge_base.json`
- V2 設計書: `docs/agent-harness/harness-v2-design.md`

### V2 データ更新責務

- Radar (`--mode v2-radar`): 記事本文を読みアイデアを抽出
- Analyze (`--mode v2-analyze`): ギャップ分析を実行
- Pipeline (`--mode pipeline`): Radar→Analyze→Review→Execute→Validate→Garden→Monitoring を実行
- レビューループスクリプト: `scripts/run_v2_review_loop.sh`

## 境界

- V2: 6ブログの記事本文を分析対象とし、補足としてZenn/Qiita/noteも参照する。
- `latest_url` と `evidence_url` は source ごとの許可プレフィックスで検証する。
- 収集失敗は許容するが、V1フォールバックは行わず失敗イベントを進捗ログへ残す。
- 不採用アイデアは理由付きで `ideas/rejected/` に永続化する。
