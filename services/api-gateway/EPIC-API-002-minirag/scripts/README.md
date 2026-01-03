# MiniRAG スクリプト使い方ガイド

このディレクトリには、MiniRAG サービスを起動・停止するためのスクリプトが含まれています。

## 前提条件

- Docker と Docker Compose がインストールされていること
- `.env` ファイルがプロジェクトルートに存在すること（必要な環境変数が設定されていること）

## スクリプト一覧

### `start.sh` - コンテナの起動

MiniRAG サービス（PostgreSQL + AGE + pgvector と MiniRAG API）を起動します。

#### 基本的な使い方

```bash
cd services/api-gateway/EPIC-API-002-minirag

# 通常起動
./scripts/start.sh

# DBをクリーンアップしてから起動（既存データを削除）。基本はこっち。
./scripts/start.sh cleanup
```

#### 動作内容

1. **通常起動モード** (`./scripts/start.sh`)
   - 既存のコンテナを起動（既に起動している場合は何もしない）
   - PostgreSQL コンテナのヘルスチェックが成功するまで待機（最大60秒）
   - `data/minirag` ディレクトリの権限を確認・修正
   - コンテナのログをリアルタイムで表示（Ctrl+C で終了、コンテナは停止しない）

2. **クリーンアップモード** (`./scripts/start.sh cleanup`)
   - 既存のコンテナ、ボリューム、イメージをすべて削除
   - `postgres/init` ディレクトリの権限を調整
   - 新しいコンテナを起動
   - 以降は通常起動モードと同じ

#### 注意事項

- スクリプト実行中に `Ctrl+C` を押すと、ログ表示のみが終了します（コンテナは停止しません）
- PostgreSQL のデータは Docker の named volume (`postgres_data`) に保存されます
- MiniRAG の作業ディレクトリは `./data/minirag` にマウントされます

---

### `stop.sh` - コンテナの停止

MiniRAG サービスを停止します。

#### 基本的な使い方

```bash
# 完全停止（データボリュームとイメージも削除）
./scripts/stop.sh

# データボリュームを保持して停止
./scripts/stop.sh keep-volumes

# データボリュームとイメージの両方を保持して停止
./scripts/stop.sh keep-all
```

#### 動作内容

1. **完全停止モード** (`./scripts/stop.sh`)
   - コンテナを停止・削除
   - データボリューム（`postgres_data`）を削除
   - Docker イメージを削除
   - **警告**: すべてのデータが失われます

2. **データ保持モード** (`./scripts/stop.sh keep-volumes`)
   - コンテナを停止・削除
   - データボリュームは保持（次回起動時にデータが残ります）
   - Docker イメージは削除

3. **完全保持モード** (`./scripts/stop.sh keep-all`)
   - コンテナを停止・削除
   - データボリュームとイメージの両方を保持
   - 次回起動時にイメージの再ビルドが不要

#### 使用例

```bash
# 開発中に一時的に停止（データは保持）
./scripts/stop.sh keep-volumes

# 次回起動時
./scripts/start.sh  # データが残っている状態で起動

# 完全にクリーンアップしたい場合
./scripts/stop.sh
# または
./scripts/start.sh cleanup
```

---

## サービスのアクセス情報

起動後、以下のエンドポイントにアクセスできます：

- **MiniRAG API**: http://localhost:8165
  - ヘルスチェック: http://localhost:8165/health
  - API ドキュメント: http://localhost:8165/docs (FastAPI の自動生成ドキュメント)

- **PostgreSQL**: localhost:5433
  - 接続情報は `.env` ファイルを参照してください

## トラブルシューティング

### コンテナが起動しない場合

```bash
# ログを確認
docker compose logs

# コンテナの状態を確認
docker compose ps

# 完全にクリーンアップして再起動
./scripts/stop.sh
./scripts/start.sh cleanup
```

### 権限エラーが発生する場合

Windows の WSL や Git Bash を使用している場合、`sudo` が必要な場合があります：

```bash
# sudo が必要な場合
sudo ./scripts/start.sh
```

### ポートが既に使用されている場合

```bash
# ポートの使用状況を確認
# Windows (PowerShell)
netstat -ano | findstr :8165
netstat -ano | findstr :5433

# Linux/WSL
lsof -i :8165
lsof -i :5433
```

既に使用されている場合は、該当プロセスを停止するか、`compose.yaml` でポート番号を変更してください。

## 関連ファイル

- `compose.yaml`: Docker Compose の設定ファイル
- `.env`: 環境変数の設定ファイル（プロジェクトルート）
- `minirag_app/`: MiniRAG アプリケーションのソースコード
- `postgres/`: PostgreSQL の初期化スクリプトとマイグレーション
