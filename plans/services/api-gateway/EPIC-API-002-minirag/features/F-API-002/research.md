# Research: F-API-002 MiniRAG構造化データ登録・検索バックエンド

## Decision 1: 永続化ストアは PostgreSQL + pgvector を採用
- Decision: PostgreSQL（pgvector有効化）を永続化ストアとして使う
- Rationale: 参考実装が PostgreSQL を前提にしており、構造化データとベクトル検索の両立が可能
- Alternatives considered: 
  - インメモリのみ（再起動耐性が満たせない）
  - SQLite（ベクトル検索運用が限定的）
  - 外部ベクトルDB（デモ用途には過剰）

## Decision 2: MiniRAG の Python 実装を利用
- Decision: MiniRAG の Python 実装（参考スクリプト）に合わせて連携する
- Rationale: 既存の参考実装が Python で提供され、DB接続と検索の流れが確認できる
- Alternatives considered:
  - 独自実装（学習コストと検証工数が増える）

## Decision 3: LLM/Embedding 設定は参考実装の既定値に合わせる
- Decision: LLM は `deepseek/deepseek-v3.2-speciale`、Embedding は `sentence-transformers/all-MiniLM-L6-v2` を既定とする
- Rationale: 参考実装で動作実績があり、デモ目的の再現性を優先
- Alternatives considered:
  - 他モデルへの置き換え（評価・調整コストが発生）

## Decision 4: API 認可は固定デモAPIキー
- Decision: すべてのエンドポイントで `X-Demo-Api-Key` を必須とする
- Rationale: デモ用途の最小限の安全策として十分
- Alternatives considered:
  - 認証なし（誤操作リスク）
  - OAuth/JWT（デモ用途には過剰）

## Decision 5: エンドポイント構成
- Decision: `/minirag` 配下に登録・検索・削除エンドポイントを置く
- Rationale: UI との連携が単純になり、デモの導線が明確
- Alternatives considered:
  - 既存APIに混在（検索系の可視性が落ちる）
