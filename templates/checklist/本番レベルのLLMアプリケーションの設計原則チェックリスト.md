# 本番レベルのLLMアプリケーションの設計原則チェックリスト

このドキュメントは、LLMアプリケーションをプロトタイプから本番で運用可能なレベルへと引き上げるための設計原則をまとめたものです。これは Heroku が提唱した [The Twelve-Factor App](https://12factor.net/) の思想を、LLMおよびエージェントの時代に合わせて再構成した**12の原則**です。

LLMエージェントを「本番品質」に引き上げる鍵は、**プロンプト・履歴・ツール呼び出しをコードと同格に扱い、ステートレスな純関数へ近づける設計と運用**にあります。これらの原則を守ることで、信頼性と拡張性を備えたLLMアプリケーションを構築できます。

## Natural Language → Tool Calls

- [ ] ツール定義の**スキーマ（JSON Schema / Pydantic / OpenAPI）**が存在し、Repoにバージョン管理されているか。
- [ ] LLMの責務が「どのツールをどの引数で呼ぶか」に限定されているか（仕様・設計の記述確認）。

## Own Your Prompts

- [ ] `libs/prompts/` 等の**プロンプト格納ディレクトリ**と**スナップショットテスト**（例：Golden/Regression）がCIに組み込まれているか。
- [ ] PRでプロンプト差分が必ずレビューに出る（Code Owners/Path Filter）か。

## Own Your Context Window

- [ ] **履歴圧縮の実装**（要約・抽出・YAML/JSON化）が存在し、ユニットテストがあるか。
- [ ] 「システム＋圧縮履歴＋現在入力」の入力設計がPlanに明文化されているか。

## Tools are Structured Outputs

- [ ] LLM出力→アプリ側の**厳格パース＆バリデーション**（型・範囲・権限）が実装され、異常時のフォールバックが定義されているか。

## Unify Execution State & Business State

- [ ] `thread_id / messages[] / metadata` の**単純なスレッド保存スキーマ**が実装され、**再開API**から復元可能か。

## Launch / Pause / Resume with Simple APIs

- [ ] `POST /threads/{id}/resume` 等の**再開API**が存在し、E2Eテストで**中断→再開**が通るか。

## Contact Humans with Tool Calls

- [ ] **人間連携ツール（Slack/Email等）**がツール定義に含まれ、返信が**スレッドに戻る**経路があるか。

## Own Your Control Flow

- [ ] 1ターン＝(LLM呼出/ツール実行/状態更新) の**純粋関数的ループ**が関数化され、**リトライ＆バックオフ**のポリシーがコード化されているか。

## Compact Errors into Context Window

- [ ] 例外の**要約インジェクション**（エラーダイジェストを次ターンに与える）実装があるか。**失敗カウンタ→エスカレーション**が設定されているか。

## Small, Focused Agents

- [ ] 1エージェントの**想定ターン数（3〜20）**がPlanで宣言され、Sub-Agent分割方針が明示されているか。

## Trigger from Anywhere

- [ ] **Cron/Webhook/Chat** などのエントリポイントがスレッドに統一的に変換される実装があるか。

## Make Your Agent a Stateless Reducer

- [ ] **ステートはスレッドのみ**に依存（サーバーローカル状態なし）で、**楽観/悲観ロック**のどちらかで整合性制御しているか。