README.md と docs/onboarding.md を確認してください。
あれば、harness/AI-Agent-progress.txt も確認してください。
また、必要に応じてブランチ作成とPUSH操作を許可します。

# --------------------------
# avatar-ui とはまだ統合せずに一旦簡易チャットUIを用意してマイクロサービスとして動くところまで持って行く。まずは Docker で MiniRAG がちゃんと動くことを目指す。
# --------------------------
/speckit.specify

### コンテキスト

temp/MiniRAGのサンプル に MiniRAG のサンプルコードを入れました。

- MiniRAG には構造化データを入れてそのデータを検索することができます
- 構造化データはポスグレで永続化されます
- LLMは deepseek/deepseek-v3.2-speciale を使います
- MiniRAGとポスグレはそれぞれDockerで起動します
- 登録・検索用のサンプルコードは「temp/MiniRAGのサンプル/minirag_app/docs/MiniRAG_on_postgres.py」です。これを参照して実装してください

### 指示

マイクロサービスとしてMiniRAGを取り込み、使えるようにしてください。MiniRAGの登録・検索はバックエンドとし、UIはHTMLベースの簡易的なチャットUIとし、構造化データのサンプルを5件用意して、この5件を登録・削除・検索できるようなUIで作ってください。
意味が分からなければ質問してください。
# --------------------------
F-API-002（MiniRAG構造化データ登録・検索バックエンド）と F-API-003（MiniRAGデモ用チャットUI）のブランチを作成してください。

/speckit.clarify F-API-002
/speckit.clarify F-API-003
# --------------------------
GitHub Issue を作成して @me にアサインしてください。タイトルは良い感じに整形してください。