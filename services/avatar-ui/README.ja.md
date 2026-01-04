UI: http://localhost:5113/

起動に4分くらいかかるが
INFO:     Started server process [482094]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:41004 - "GET /agui/config HTTP/1.1" 200 OK
INFO:     127.0.0.1:41004 - "OPTIONS /agui/diary/search-settings HTTP/1.1" 200 OK
INFO:     127.0.0.1:41016 - "POST /agui/diary/search-settings HTTP/1.1" 200 OK
が出ればOK。画面のアバター名も変わる。

- WSL 内で:  
  `curl http://127.0.0.1:1686/healthz`

- Windows 側ブラウザで:  
  [http://localhost:1686/healthz](http://localhost:1686/healthz)



# AVATAR UI

人と AI が共存する次世代インターフェース基盤。  
OpenRouter / Gemini / OpenAI / Anthropic 対応。デスクトップで動くエージェント UI。

![demo](./docs/assets/avatar-ui_demo_02.gif)

## 特徴

- **マルチLLM対応** – OpenRouter / Gemini / OpenAI / Anthropic を設定で切り替え
- **ツール拡張対応** – 検索エージェント標準搭載。MCP連携・ツール追加可
- **パーソナライズUI** – 3種のカラーテーマ。アバター変更も自由
- **デスクトップアプリ** – ローカル動作。macOS / Windows / Linux 対応
- **商用利用可** – オープンソース（MIT）。個人・商用問わず自由に利用可能
- **日記 + MiniRAG 連携** – 会話確定ボタンで日記を構造化し MiniRAG に登録、必要時に過去日記のコンテキストを取得
- **プロファイリング更新** – 会話確定後にユーザーの発話を分析し、固定プロファイルを差分更新（失敗時は警告表示）

## 使い方

1. アプリ起動 → アバターが待機状態で表示
2. メッセージ入力 → `Enter` で送信
3. アバターがリアルタイム応答
4. Web検索トグルが ON の場合、必要に応じて Google 検索を自動実行
5. 終了：`Ctrl+C`

## 日記 + MiniRAG 連携（概要）

- UI に「MiniRAG検索トグル」「Web検索トグル」「top_k 設定」「会話確定ボタン」が表示されます。
- 会話確定ボタンを押すと、メイン LLM が会話内容を分析し、重要度・サマリー・記憶を抽出します。
- 抽出結果は MiniRAG に構造化データとして登録されます。
- MiniRAG検索トグル ON のときのみ、MiniRAG 検索で過去日記を参照します。
- Web検索トグル ON のときのみ、Gemini による Web 検索を実行し、その結果を OpenRouter のユーザーコンテキストに注入します。
- top_k と MiniRAG検索トグルの初期値は `settings.json5` の `minirag` セクションで調整できます。
- 会話確定後にユーザー発話のみを分析し、`profiling/user_profile.yaml` が差分更新されます。

## クイックスタート

## DeepAgentsSpec での配置

このリポジトリでは、`services/avatar-ui/` に配置済みです。
以下はこの構成に合わせた最小手順です。

### 1. 環境変数を用意（必須）

`services/avatar-ui/` 直下に `.env` を作成し、必要な環境変数を設定してください。
主な必須項目は以下です（値はあなたの環境に合わせて設定）:

- `OPENROUTER_API_KEY`（OpenRouter を使う場合）
- `GOOGLE_API_KEY`（検索サブエージェントを使う場合）
- `AGENT_ID`
- `THREAD_ID`
- `SERVER_HOST`
- `SERVER_BIND_HOST`（任意、WSL などで 0.0.0.0 バインドしたい場合）
- `SERVER_PORT`
- `CLIENT_PORT`
- `APP_ENV`
- `SESSION_TIMEOUT_SECONDS`
- `CLEANUP_INTERVAL_SECONDS`

> 注意: 検索サブエージェントが有効な場合、`GOOGLE_API_KEY` が未設定だと起動時にエラーになります。
> WSL で Windows 側ブラウザからアクセスする場合は `SERVER_BIND_HOST=0.0.0.0` を設定してください。

### 2. 設定ファイル（任意）

`settings.default.json5` を元に `settings.json5` を用意すると設定を上書きできます。

### 3. 起動（開発 / Webブラウザ）

以下のどちらかで起動できます。

- サービス付属スクリプト（推奨）:

```bash
cd services/avatar-ui
# 初回のみ
cd app && npm install
cd ..
./scripts/run_dev.sh
```

- 手動起動:

```bash
# サーバー
cd services/avatar-ui/server
# 初回のみ（依存の取得）
uv pip show ag-ui-protocol fastapi uvicorn
uv pip install --link-mode=copy -e .
uv run --link-mode=copy python main.py

# 別ターミナルでクライアント
cd services/avatar-ui/app
npm install
npm run dev
```

> `uv` が未インストールの場合は `python main.py` を利用してください。
> Electron ではなく Web ブラウザで動作させるため、`AVATAR_UI_WEB_ONLY=1` が自動で有効になります。

### 必要なもの

- Node.js 20+
- Python 3.12+
- API キー（いずれか1つ以上）
  - [OpenRouter](https://openrouter.ai/keys)
  - [Gemini](https://aistudio.google.com/app/apikey)
  - [OpenAI](https://platform.openai.com/api-keys)
  - [Anthropic](https://console.anthropic.com/settings/keys)

> ⚠️ 外部 API（OpenRouter / Gemini / OpenAI / Anthropic 等）の利用は各サービスの利用規約に従ってください。API キーは本リポジトリに含まれていません。

### 1. リポジトリを取得

GitHub からソースコードをダウンロードします（`git clone` コマンド）。

```bash
git clone https://github.com/siqidev/avatar-ui.git
cd avatar-ui
```

### 2. 環境変数を設定

API キーなどの秘密情報を `.env` ファイルに保存します。  
まずテンプレートをコピー:

```bash
cp .env.example .env
```

`.env` を開き、使用する LLM の API キーを設定:

```dotenv
OPENROUTER_API_KEY=your-api-key-here
# 検索サブエージェントを使う場合は Gemini のキーも設定
GOOGLE_API_KEY=your-api-key-here
# OpenAI / Anthropic を使う場合は対応するキーも設定
```

### 3. セットアップと起動

#### macOS / Linux

```bash
# プロジェクトのルートへ移動（あなたのパスに置き換えてください）
# 例：Documents フォルダに配置した場合
cd ~/Documents/avatar-ui

# サーバー準備（Python 仮想環境を作成し、依存をインストール）
cd server
python3 -m venv .venv   # 初回のみ
source .venv/bin/activate
pip install -e .        # 初回のみ

# 起動（サーバー + クライアント同時）
cd ../app
npm install             # 初回のみ
npm run dev:all
```

#### Windows (PowerShell)

```powershell
# プロジェクトのルートへ移動（あなたのパスに置き換えてください）
# 例：Documents フォルダに配置した場合
cd "$HOME\Documents\avatar-ui"

# サーバー準備（Python 仮想環境を作成し、依存をインストール）
cd server
python -m venv .venv    # 初回のみ
.\.venv\Scripts\Activate.ps1
pip install -e .        # 初回のみ

# 起動（サーバー + クライアント同時）
cd ..\app
npm install             # 初回のみ
npm run dev:all
```

起動すると Electron アプリが自動で開きます。開発中はターミナルに表示される URL（例: `http://localhost:5173`）からブラウザでも確認できます。

## 設定

設定ファイルをコピーして編集します:

```bash
cp settings.default.json5 settings.json5
```

`settings.json5` で LLM やテーマなどを変更できます。

### LLM の切り替え

```json5
"server": {
  "llmProvider": "openrouter",   // gemini | openai | anthropic | openrouter
  "llmModel": "deepseek/deepseek-v3.2-speciale"
}
```

対応する API キーを `.env` に設定し、サーバーを再起動してください。
OpenRouter を使う場合、`llmModel` は `openrouter/` のプレフィックスなしでも指定できます（内部で自動補完）。
OpenRouter の一部モデルは tools に非対応のため、`llmProvider=openrouter` の場合はツール呼び出しを行わずに実行します。
Web検索トグルが ON のスレッドでは Gemini で Web 検索を実行し、その結果を OpenRouter のユーザーコンテキストに注入します。

reasoning を切り替える場合:

```json5
"server": {
  "reasoning": {
    "enabled": true
  }
}
```

### 検索サブエージェント

デフォルトで Google 検索サブエージェントが有効です（Gemini モデルで動作）。  
Web検索トグルが ON のときにのみ、このサブエージェントが呼び出されます。  
無効化する場合:

```json5
"searchSubAgent": {
  "enabled": false
}
```

検索サブエージェントは Gemini API を使用するため、利用には `GOOGLE_API_KEY` の設定が必要です。
必要に応じて `provider` / `model` を上書きできます:

```json5
"searchSubAgent": {
  "enabled": true,
  "provider": "gemini",
  "model": "gemini-2.5-flash"
}
```

### Web検索トグル

Web 検索の初期状態は `settings.json5` の `webSearch` セクションで調整できます。

```json5
webSearch: {
  enabledDefault: true
}
```

### 日記 + MiniRAG 設定

`settings.json5` の `minirag` セクションで、MiniRAG の接続先と UI のデフォルト値を設定できます。

```json5
minirag: {
  baseUrl: "http://localhost:8165",
  workspace: "diary",
  searchEnabledDefault: true,
  topKDefault: 3,
}
```

### プロファイリング設定

`settings.json5` の `profiling` セクションで、プロファイル更新に使うモデルと反映の最低信頼度を設定できます。

```json5
profiling: {
  model: "deepseek/deepseek-v3.2-speciale",
  minConfidence: 0.6,
}
```

### カスタマイズ一覧

| 項目 | 設定場所 |
|------|----------|
| システムプロンプト | `settings.json5` → `server.systemPrompt` |
| テーマ・色 | `settings.json5` → `ui.theme`, `ui.themes` |
| アバター画像 | `app/src/renderer/assets/` に配置 |
| ツール追加 | `server/main.py` → `tools` リスト |

## ドキュメント

- [設計書](./docs/project.md) – アーキテクチャ、実装詳細、ロードマップ
- [AG-UI Protocol](https://docs.ag-ui.com/) – プロトコル仕様（公式）
- [Google ADK](https://google.github.io/adk-docs/) – エージェント開発キット（公式）

## ライセンス

[MIT License](LICENSE)

© 2025 [SIQI](https://siqi.jp) (Sito Sikino)

## メモ

フロントエンド（Vite/ブラウザ）と Python（FastAPI）は、それぞれ別プロセスとして同時に起動しています。  
`services/avatar-ui/scripts/run_dev.sh` は、まず Python サーバー（FastAPI）をバックグラウンドで起動し、次に Vite（フロントエンド）をフォアグラウンドで起動します。

起動の流れ（概要）:

1. Python（FastAPI）が `SERVER_HOST:SERVER_PORT` で待機
2. Vite が `CLIENT_PORT` で待機
3. ブラウザは Vite にアクセス
4. Vite は `/agui` への通信を Python サーバーにプロキシ

このプロキシの設定は `services/avatar-ui/app/vite.config.ts` に記載されています。  
つまり、「UI はブラウザで動作し、API は Python で提供される」構成となっています。

起動状況の確認方法:

- Vite:  [http://localhost:CLIENT_PORT](http://localhost:CLIENT_PORT)
- Python: [http://SERVER_HOST:SERVER_PORT/healthz](http://SERVER_HOST:SERVER_PORT/healthz)
