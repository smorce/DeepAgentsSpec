# Avatar UI サービスアーキテクチャ

このサービスは、ユーザー向けの UI と AG-UI サーバーを同梱したマイクロサービスです。
デスクトップ（Electron）とブラウザ（Vite）で同じ UI を提供し、
FastAPI ベースのサーバーが AG-UI プロトコルを提供します。
日記会話を構造化して MiniRAG に登録し、必要時に過去日記の検索コンテキストを取得するフローも担当します。

## 構成

- `app/`: Electron + Vite のフロントエンド。
- `server/`: FastAPI + AG-UI ADK ブリッジ。
- `settings.default.json5`: UI/サーバー共通の設定デフォルト。
- `profiling/`: 固定項目のユーザープロファイル（YAML）と初期テンプレート。
- MiniRAG 連携: 日記会話の確定登録と検索コンテキスト取得。

## 起動モデル

- `server/` を起動し、`/agui` と `/agui/config` を提供します。
- `app/` は `SERVER_HOST`/`SERVER_PORT` を参照して AG-UI サーバーに接続します。
- 開発時は `app/` の Vite サーバーが `CLIENT_PORT` で起動し、`/agui` をプロキシします。
- 会話確定時は `/agui/diary/finalize` を呼び、MiniRAG に日記を登録します。
- MiniRAG 登録成功後に、ユーザー発話を分析してプロファイルを更新します。
- 検索トグルの変更は `/agui/diary/search-settings` を通じて反映します。

## 依存関係

- Python 3.12+（サーバー）
- Node.js 20+（クライアント）
- 環境変数（`.env` で提供）
- MiniRAG API（`/minirag/documents/bulk`, `/minirag/search`）

詳細な設定は `README.ja.md` を参照してください。
