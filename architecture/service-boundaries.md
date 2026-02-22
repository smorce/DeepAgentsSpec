# サービス境界

## V1 境界定義

### A. Source Radar

責務:
- 6ブログの更新収集
- 差分検知

非責務:
- 実装コード自体の改変（V2 Executor の責務）
- 未許可ソースの収集

主な成果物:
- `harness/agent_radar/snapshot-latest.json`
- `harness/agent_radar/new-items.json`

### B. Harness Validator

責務:
- 許可URL境界の検証
- SoR構造の整合性検証

非責務:
- 仕様策定そのもの

主な成果物:
- バリデーション結果（終了コード/標準出力）

### C. Doc Gardener

責務:
- SoR文書の劣化検知（TODO、未確定記法）
- `experiment_backlog.json` と `docs/agent-harness/autonomous-growth.md` の同期維持

非責務:
- 新機能実装

### D. State Persistence

責務:
- ホット状態/コールド状態の分離保存
- 差し替え表現の一貫管理

非責務:
- 機密値の保存

## V2 境界定義

### E. Article Analyzer（V2 Radar）

責務:
- 記事本文の読み込みとハーネスエンジニアリングアイデアの抽出
- 補足情報源（Zenn/Qiita/note）からの追加情報収集
- ナレッジベースとの重複検出

非責務:
- アイデアの採否判定（Gap Analyzer の責務）
- 実行計画の作成

主な成果物:
- `harness/agent_radar/ideas/IDEA-*.json`
- `harness/agent_radar/knowledge_base.json`

### F. Gap Analyzer

責務:
- アイデアとコードベースのギャップ分析（現状→理想→差分）
- 採否判定と不採用理由の記録

非責務:
- 実行計画の作成（Review Loop の入力として Plan Drafter が担当）
- コードの直接改修

主な成果物:
- `harness/agent_radar/analysis/GAP-*.json`
- `harness/agent_radar/ideas/rejected/IDEA-R*.json`

### G. Review Loop

責務:
- 実行計画の多段レビュー（5軸評価）
- 計画の段階的改善（修正エージェントによるフィードバック反映）
- 完了/不採用/要人間レビューの判定

非責務:
- 計画の実行

主な成果物:
- `harness/agent_radar/reviews/REV-*/plan.md`
- `harness/agent_radar/reviews/REV-*/review-session-*.md`
- `harness/agent_radar/reviews/REV-*/status.json`

### H. Executor

責務:
- レビュー通過した計画に基づくコードベースの改修
- ディレクトリ構造変更のSoR化（マークダウン→スクリプト→実行）
- ロールバックスクリプトの生成

非責務:
- 計画の策定やレビュー
- 禁止操作（`rm -rf`, `git reset --hard` 等は AGENTS.md の禁止事項に従う）

主な成果物:
- `harness/agent_radar/executions/EXEC-*/dir-structure.md`
- `harness/agent_radar/executions/EXEC-*/change-script.py`
- `harness/agent_radar/executions/EXEC-*/rollback-script.py`
- `harness/agent_radar/executions/EXEC-*/result.json`

## 境界違反の扱い

- 許可外URLを検出した場合は即失敗（非0終了）。
- V2 Executor が AGENTS.md の禁止操作を行おうとした場合は即失敗。
- 失敗イベントは `harness/AI-Agent-progress.txt` に残す。
