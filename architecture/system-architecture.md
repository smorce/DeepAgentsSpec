# システムアーキテクチャ

## 目的

このリポジトリは、AIエージェントによる長期自律開発を維持するためのハーネスを、リポジトリ内だけで継続進化させることを目的とします。
中心思想は「コードを書く前に、環境・意図・フィードバックループを設計する」です。

## システム構成

### V2 レイヤー（自律的ハーネスエンジニアリング改良）

1. Article Analysis Layer
   - 公式ブログの記事本文をCodex CLIで読み、ハーネスエンジニアリングに適用可能なアイデアを抽出する。
   - 補足として Zenn/Qiita/note の解説記事も参照する。
   - SoR: `harness/agent_radar/ideas/`, `harness/agent_radar/knowledge_base.json`

2. Gap Analysis Layer
   - 抽出したアイデアを現在のコードベースと突き合わせ、現状→理想→差分のギャップ分析を行う。
   - 不採用アイデアは理由付きで永続化する。
   - SoR: `harness/agent_radar/analysis/`, `harness/agent_radar/ideas/rejected/`

3. Review Loop Layer
   - 採用アイデアの実行計画を Codex CLI 非対話モードのマルチセッションで多段レビューする。
   - 5軸評価（ハーネス関連性/実現可能性/リスク/ROI/SoR整合性）で判定する。
   - SoR: `harness/agent_radar/reviews/`

4. Execution Layer
   - レビュー通過した計画を、タスク単位の隔離worktreeで再現→修正→検証→証跡化まで一括実行する。
   - SoR: `harness/agent_radar/executions/`
   - 設計書: `docs/agent-harness/harness-v2-design.md`

5. Quality & Gardening Layer
   - すべての実行後に `validate` と `garden` を実行する。
   - 失敗時は整合回復を試行し、結果を `self_heal_log.json` に記録する。

6. Monitoring Layer
   - `metrics/latest.json` と `monitoring_results.json` を更新し、品質傾向を可視化する。

## データフロー

### V2 フロー

- Radar が記事本文を分析し `ideas/IDEA-*.json` へアイデアを保存
- Analyzer がギャップ分析を行い `analysis/GAP-*.json` へ結果を保存（不採用は `ideas/rejected/` へ）
- Review Loop が計画を多段評価し `reviews/REV-*/` へセッション記録を蓄積
- Executor がworktree隔離実行で改修し `executions/EXEC-*/` と `harness/worktree/runs/*` へ証跡を保存
- validate/garden で改修後の整合性を検証し、監視結果を更新

### 統合フロー

- `pipeline` は V2単体で完結する
- 人間判断が必要なものだけをエスカレーション

## 設計原則

- Source boundary first: 指定された公式URL以外を学習ソース化しない（V2では補足としてZenn/Qiita/noteも参照）。
- Progressive disclosure: AGENTS.mdは目次化し、詳細は docs/plans へ分離。
- Mechanical enforcement: ルールは文書化だけでなくスクリプトで検証する。
- State externalization: 長文状態は会話に埋めず、参照トークン化する。
- Rejected idea preservation: 不採用アイデアも理由付きで永続化し、将来の再検討に備える。
- Multi-session review: 計画は毎回コンテキストをリセットした独立セッションで複数回レビューする。
- No fallback concealment: 失敗はフォールバックで隠さず、観測可能な証跡として残す。
