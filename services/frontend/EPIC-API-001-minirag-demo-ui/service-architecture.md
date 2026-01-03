# MiniRAG Demo UI サービスアーキテクチャ

このサービスは、静的HTML/JSのみで構成されるデモ用チャットUIを提供する。
最小のHTTPサーバーで配信し、MiniRAGバックエンド（api-gateway）に対して
登録・検索・削除のリクエストを送る。

## 構成

- `public/`: 配信用の静的アセット（HTML/CSS/JS）
- `src/`: 必要に応じてJSの分割やユーティリティを配置
- `scripts/`: ローカル配信用の簡易サーバー起動スクリプト

## 依存関係

- ビルド工程なし（静的ファイル）
- 最小HTTPサーバー（例: python -m http.server など）
- MiniRAGバックエンド（`services/api-gateway`）
