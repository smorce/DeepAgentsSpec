# Data Model: F-API-003 MiniRAGデモ用チャットUI

## Entities

### SampleStructuredRecord
- **Purpose**: UI に表示する構造化データ
- **Fields**:
  - `doc_id` (string, required)
  - `title` (string, required)
  - `summary` (string, required)
  - `body` (string, required)
  - `status` (string, required)
  - `region` (string, optional)
  - `priority` (integer, optional)
  - `created_at` (ISO-8601 datetime, required)
  - `metadata` (object, optional)

### ChatMessage
- **Purpose**: チャット履歴の表示単位
- **Fields**:
  - `role` (string, required)  # user | system | error
  - `content` (string, required)
  - `timestamp` (ISO-8601 datetime, required)

## Relationships
- UI は検索結果（SearchResult）を `SampleStructuredRecord` に変換して表示

## Validation Rules
- `content` は空文字不可
- `role` は `user` / `system` / `error` のみ

## State Transitions
- ChatMessage は追加のみ（編集/削除はしない）

## Data Volume / Scale
- デモ用途のため、履歴は 100 件までを上限とする（それ以上は古い順に破棄）
