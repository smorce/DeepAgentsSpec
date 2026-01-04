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




settings.json5 のsystemPrompt にも対応していますか？ していなければ対応してください。
あと、openrouter に検索サブエージェント機能はないので、検索が必要なケースもあって、その場合は元々あった Gemini の検索機能 を呼び出せるかな？
基本的には Gemini から移行したいですが、検索機能は Gemini を使いたいです。



