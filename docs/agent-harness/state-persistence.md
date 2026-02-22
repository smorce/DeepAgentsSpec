# 状態管理・永続化ポリシー

## 中心課題

AIエージェント実装では、「いつ・何を・どこへ退避し、会話側をどの表現へ差し替えるか」を固定しないと、長期運用時にコンテキストが崩壊します。
本リポジトリでは、会話と状態を分離し、状態参照をトークン化します。

## いつ退避するか

以下のタイミングでチェックポイントを作成します。

- 実装フェーズ切替（設計→実装、実装→検証）
- 長時間ジョブ開始前
- 外部I/Oリトライが閾値を超えた時
- 人間承認待ちに入る時
- V2 レビューセッション完了時（各セッションの結果を即座に永続化）
- V2 Execute 完了時（変更結果とロールバック情報を永続化）

## 何を退避するか

- 実行に必要な最小状態（タスクID、入力要約、生成物参照、次アクション）
- ツール実行結果の要約（生ログ全量は保存しない）
- 失敗原因の圧縮サマリ
- V2 レビュースコアと verdict（判定結果）
- V2 ギャップ分析の verdict と reason

保存しないもの:

- `.env` 相当の機密値
- トークン/秘密鍵/個人識別情報
- Codex CLI の stdout 全量（要約のみ保存）

## どこへ退避するか

### V1 状態

- Hot tier: `harness/agent_radar/state.json`（最新状態）
- Cold tier: `harness/agent_radar/archive/YYYY/MM/*.jsonl`（履歴）

### V2 状態

- アイデア: `harness/agent_radar/ideas/IDEA-*.json`（Hot — 個別ファイル）
- 不採用アイデア: `harness/agent_radar/ideas/rejected/IDEA-R*.json`（Hot — 理由付き永続化）
- ギャップ分析: `harness/agent_radar/analysis/GAP-*.json`（Hot — 分析結果）
- レビューステータス: `harness/agent_radar/reviews/REV-*/status.json`（Hot — セッション進行状態）
- レビュー履歴: `harness/agent_radar/reviews/REV-*/review-session-*.md`（Cold — 各セッションの記録）
- 実行結果: `harness/agent_radar/executions/EXEC-*/result.json`（Hot — 変更結果とエラー）
- ナレッジベース: `harness/agent_radar/knowledge_base.json`（Hot — 重複検出用蓄積データ）

## 会話側の差し替え表現

会話本文には状態本体を埋めず、次の形式で参照します。

- `[[STATE_REF:state_id]]`
- `[[PLAN_REF:EPIC-ID/FEATURE-ID]]`
- `[[EVAL_REF:run_id]]`
- `[[IDEA_REF:IDEA-NNN]]`（V2 アイデア参照）
- `[[GAP_REF:GAP-IDEA-NNN]]`（V2 ギャップ分析参照）
- `[[REVIEW_REF:REV-EXP-NNN]]`（V2 レビューステータス参照）

例:

- `会話状態は [[STATE_REF:st_20260213_001]] を参照。`
- `ギャップ分析結果は [[GAP_REF:GAP-IDEA-001]] を参照。`

## スキーマ

`harness/agent_radar/runtime_state_schema.json` を唯一のスキーマとして使用します。
