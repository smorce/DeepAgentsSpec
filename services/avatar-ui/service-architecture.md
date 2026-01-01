# Avatar UI サービスアーキテクチャ

このサービスは、ユーザー向けの UI と AG-UI サーバーを同梱したマイクロサービスです。
デスクトップ（Electron）とブラウザ（Vite）で同じ UI を提供し、
FastAPI ベースのサーバーが AG-UI プロトコルを提供します。

## 構成

- `app/`: Electron + Vite のフロントエンド。
- `server/`: FastAPI + AG-UI ADK ブリッジ。
- `settings.default.json5`: UI/サーバー共通の設定デフォルト。

## 起動モデル

- `server/` を起動し、`/agui` と `/agui/config` を提供します。
- `app/` は `SERVER_HOST`/`SERVER_PORT` を参照して AG-UI サーバーに接続します。
- 開発時は `app/` の Vite サーバーが `CLIENT_PORT` で起動し、`/agui` をプロキシします。

## 依存関係

- Python 3.12+（サーバー）
- Node.js 20+（クライアント）
- 環境変数（`.env` で提供）

詳細な設定は `README.ja.md` を参照してください。
