#!/bin/bash
# start.sh - Dockerコンテナを起動するスクリプト

# 引数の確認
CLEANUP_DB=false
if [ "$1" = "cleanup" ]; then
    CLEANUP_DB=true
    echo "DBクリーンアップモードで起動します..."
fi

# sudo 実行時は SUDO_UID/SUDO_GID を優先し、ホストユーザーを特定
HOST_UID="${SUDO_UID:-$(id -u)}"
HOST_GID="${SUDO_GID:-$(id -g)}"
POSTGRES_GID=999

if [ "$HOST_UID" = "0" ]; then
    echo "警告: ホストUIDが0です。rootで実行している可能性があります。所有権の設定に注意してください。" >&2
fi

echo "権限設定: ホストUID:GID=${HOST_UID}:${HOST_GID}, PostgreSQL GID=${POSTGRES_GID}"

# DBクリーンアップの実行
if [ "$CLEANUP_DB" = true ]; then
    echo "PostgreSQLデータボリュームをクリーンアップしています..."
    
    # 既存のコンテナを停止・削除（named volumeも削除される）
    docker compose down --volumes --rmi all
    
    # init スクリプト・マイグレーション用ディレクトリの権限を調整
    if [ -d "./postgres" ]; then
      echo "postgres/init ディレクトリの権限を確認中..."
      sudo chown -R ${HOST_UID}:${HOST_GID} ./postgres
      chmod -R 755 ./postgres
    fi
    
    echo "PostgreSQLボリュームのクリーンアップが完了しました"
fi

echo "PostgreSQL + AGE + pgvector コンテナと MiniRAG コンテナを起動します..."

# compose.yaml を使用してコンテナを起動
# 注意: compose.dev.yml は存在しないため、常に compose.yaml を使用
# --build を付けることで、ソースコードに変更があればそのレイヤー以降が再ビルドされます。
# 依存関係に変更がない限り、重い pip install はキャッシュが利用されるため高速です。
docker compose up -d --build

# PostgreSQLコンテナのhealthcheckが成功するまで待機（最大60秒）
echo "PostgreSQLコンテナの起動を待機中..."
MAX_WAIT=60
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if docker compose ps postgres | grep -q "healthy"; then
        echo "PostgreSQLコンテナが正常起動しました"
        break
    fi
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    echo -n "."
done
echo ""

# data/minirag ディレクトリの権限を確認・修正（Windowsエクスプローラーからアクセス可能にするため）
if [ -d "./data/minirag" ]; then
    echo "data/minirag ディレクトリの権限を確認中..."
    if [ "$(stat -c '%u' ./data/minirag 2>/dev/null)" != "$HOST_UID" ]; then
        echo "data/minirag ディレクトリの所有権をホストユーザーに修正中..."
        sudo chown -R ${HOST_UID}:${HOST_GID} ./data/minirag
        chmod -R 755 ./data/minirag
        echo "所有権の修正が完了しました"
    fi
else
    echo "data/minirag ディレクトリを作成中..."
    mkdir -p ./data/minirag
    sudo chown -R ${HOST_UID}:${HOST_GID} ./data/minirag
    chmod -R 755 ./data/minirag
fi

# 起動したコンテナのログをフォアグラウンドで表示
echo ""
echo "=== コンテナの起動ログ（リアルタイム表示） ==="
echo "Ctrl+C でログ表示を終了できます（コンテナは停止しません）"
echo ""
docker compose logs -f --tail=30