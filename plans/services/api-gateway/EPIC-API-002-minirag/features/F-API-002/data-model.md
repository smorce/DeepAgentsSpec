# Data Model: F-API-002 MiniRAG構造化データ登録・検索バックエンド

## Entities

### StructuredDocument
- **Purpose**: 構造化データの登録・検索対象
- **Identity**: `workspace + doc_id` の複合一意
- **Fields**:
  - `workspace` (string, required)
  - `doc_id` (string, required)
  - `title` (string, required)
  - `summary` (string, required)
  - `body` (string, required)
  - `status` (string, required)
  - `region` (string, optional)
  - `priority` (integer, optional)
  - `created_at` (ISO-8601 datetime, required)
  - `metadata` (object, optional)

- **Validation Rules**:
  - `workspace` と `doc_id` は空文字不可
  - `title` / `summary` / `body` は空文字不可
  - `priority` は 1〜5 の範囲（未指定可）
  - `created_at` は ISO-8601 形式

### SearchResult
- **Purpose**: 検索結果の表示
- **Fields**:
  - `doc_id` (string, required)
  - `title` (string, required)
  - `summary` (string, required)
  - `relevance` (number, required)
  - `source_fields` (array[string], optional)

## Relationships
- `StructuredDocument` は検索インデックス（ベクトル/メタデータ）と 1:1

## State Transitions
- `StructuredDocument` の状態遷移は本機能で管理しない（外部定義）

## Data Volume / Scale
- デモ用途のため 5 件の固定サンプルが主対象
