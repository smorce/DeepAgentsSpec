services/avatar-ui について理解してください。

### やりたいこと

services/avatar-ui は LLM として Gemini を使っていますが、これを Openrouter に変更したいです。
Openrouter は各種LLMプロバイダーでありますが、使うモデルは "deepseek/deepseek-v3.2-speciale" とします。
.env に OPENROUTER_API_KEY は設定しました。
デフォルトは "reasoning": {"enabled": True} でお願いします。

services/avatar-ui は LiteLLM をサポートしており、LiteLLM は Openrouter をサポートしているので移行はスムーズのはずです。

# LiteLLM の Openrouter の使い方
```
import os
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "ダミー")
OPENROUTER_LLM = os.getenv("OPENROUTER_LLM", "deepseek/deepseek-v3.2-speciale")

from litellm import completion

# LiteLLM は OPENROUTER_API_KEY を環境変数から読めます（明示してもOK）
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY   # 意味ないか？

resp = completion(
    # OpenRouter 経由で呼ぶので "openrouter/" を前につける
    model=f"openrouter/{OPENROUTER_LLM}",
    messages=[
        {"role": "user", "content": "How many r's are in the word 'strawberry'?"}
    ],

    # OpenRouter の reasoning を有効化（あなたの元コードと同じ意図）
    reasoning={"enabled": True},

    # “思考トレースを返す”系は OpenRouter 側で include_reasoning が必要な場合があります
    include_reasoning=True,
)

# LiteLLM: 通常の回答
print(resp.choices[0].message.content)

# LiteLLM: 推論テキストは標準化されて reasoning_content に入ることがあります
# （プロバイダ/モデルによっては message.reasoning に入る場合もあるので両方見ます）
print(getattr(resp.choices[0].message, "reasoning_content", None))   # 基本はこっちでOK
print(getattr(resp.choices[0].message, "reasoning", None))           # 念の為、こっちも見る
```

上記を参考にコードを修正してください。








- 変更は services/avatar-ui のみで良いです
- 会話内容は私の日記です。登録したいのは、その日のあったことの重要度 (1-10、LLMが一般的にみて特異性がどの程度あったかで判断)、日記サマリー、Geminiとやり取りした全文、セマンティック記憶、エピソード記憶、メタデータ(内容はあなたが考えてください)です。
これらのデータを登録するには Geminiと会話 → 会話が終了した判定 → Gemini が会話内容を分析(重要度をつけたりエピソード記憶やセマンティック記憶を抽出したり) → MiniRAG に構造化データを登録 というフローをたどる必要があります。
services/avatar-ui はあくまでもGeminiを使った会話しかできないので諸々の改修が必要ですね。
- 会話が終了した判定 はボタンにしてください。私がボタンをクリックします。
- 検索の発火条件 は Gemini に自律的に判断させたいです。また検索のON/OFFはトグルで設定したいです。
-  Gemini への渡し方は 本文、doc_id、サマリーで、上位3件（3は設定可能）です
- workspace は 固定



- services/avatar-ui に渡すコンテキストは、ユーザー入力の本文です。MiniRAGで検索した結果 Gemini に渡すコンテキストは  doc_id / summary / body の上位N件（デフォルト3）                                                      
- workspace名：diary
- EPIC/Feature ID は上記の案でOK


# =========================================
あなたは担当機能の実装エージェントです。

【機能名】avatar-ui の改修
【指示書】services/avatar-ui/issues/ISSUE-AVATAR-001-001.md
【ドキュメント】
  - README.md
  - docs/onboarding.md
  - harness/AI-Agent-progress.txt
【やること】
  1. README.mdを確認する
  2. onboarding.mdを確認する
  3. AI-Agent-progress.txtを確認する
  4. tasks.md を読み、最大限効率化しながら優先度順にタスクを実行してください。
# =========================================
プロファイリング機能を追加したいです。

仕様：
会話が確定して日記が登録されるたびに、Gemini がユーザーの価値観、思考傾向、言葉遣いなどを分析し、プロファイリングデータを更新する。
更新対象は services/avatar-ui/profiling/user_profile.yaml で、項目は固定です。
会話内容を分析して構造化するのと同じように、Gemini が会話からプロファイル更新用データを作成する必要があります。分析対象はユーザーの入力だけで良いです。

この機能を追加するためのPlanを作成してください。
意味が分からなければ質問してください


EPIC-AVATAR-001-diary-minirag に追加で。
「全体を再生成して上書き」か「項目単位で差分更新」かについては、より安定性の高い方を選択してください。全体をまるっと更新した方が安定性は高いような気がしますが、どうでしょうか？ (出力形式 の質問も同様です。)
既定値がある場合は原則”上書き”したいですが、絶対に空には戻さないでください。項目で空のものがあり、今回の更新対象でなければ空のままで問題ありません。いつか更新されるはずなので。
1ユーザー=1ファイル固定で良いです。私しか使わないので。
MiniRAG登録失敗時はプロファイル更新しない方針で。
使用モデルは Gemini で。
ファイルロック/排他制御は不要です。
# =========================================
あなたは担当機能の実装エージェントです。

【機能名】プロファイリング機能の追加
【指示書】services/avatar-ui/issues/ISSUE-AVATAR-002-001.md
【ドキュメント】
  - README.md
  - docs/onboarding.md
  - harness/AI-Agent-progress.txt
【やること】
  1. README.mdを確認する
  2. onboarding.mdを確認する
  3. AI-Agent-progress.txtを確認する
  4. tasks.md を読み、最大限効率化しながら優先度順にタスクを実行してください。
# =========================================
@services/avatar-ui/patch/mychange1.patch git apply してください。その際、--ignore-whitespace --3wayオプションを使用して適用してください。