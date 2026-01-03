#!/bin/bash
# stop.sh - Dockerコンテナを停止・削除するスクリプト

echo "PostgreSQL + AGE + pgvector コンテナと MiniRAG コンテナを停止します..."

# 引数の確認
KEEP_VOLUMES=false
KEEP_IMAGES=false
if [ "$1" = "keep-volumes" ]; then
    KEEP_VOLUMES=true
    echo "データボリュームは保持します..."
elif [ "$1" = "keep-all" ]; then
    KEEP_VOLUMES=true
    KEEP_IMAGES=true
    echo "データボリュームとイメージは保持します..."
fi

# コンテナの停止とネットワークの削除
if [ "$KEEP_VOLUMES" = true ] && [ "$KEEP_IMAGES" = true ]; then
    # ボリュームとイメージを保持
    docker compose down
elif [ "$KEEP_VOLUMES" = true ]; then
    # ボリュームを保持、イメージは削除
    docker compose down --rmi all
elif [ "$KEEP_IMAGES" = true ]; then
    # ボリュームを削除、イメージは保持
    docker compose down --volumes
else
    # デフォルト: ボリュームとイメージも削除（完全クリア）
    echo "警告: データボリュームとイメージも削除されます。"
    echo "データを保持する場合は 'keep-volumes' または 'keep-all' を引数に指定してください。"
    docker compose down --volumes --rmi all
fi

echo "コンテナを停止しました。"