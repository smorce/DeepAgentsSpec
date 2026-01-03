# Data Model: F-AVATAR-001

## Entity: DiaryEntry (MiniRAG StructuredDocument)

**Purpose**: 日記会話を MiniRAG に登録するための構造化データ。

**Fields**:

- workspace (string, required) — 固定値 `diary`
- doc_id (string, required) — `journal-YYYYMMDD-HHMMSS-<short>` 形式
- title (string, required) — Gemini が生成する日記タイトル
- summary (string, required) — Gemini が生成する日記サマリー
- body (string, required) — 「会話全文 + セマンティック記憶 + エピソード記憶」を連結
- importance_score (integer, 1-10, required) — 重要度
- semantic_memory (string, required) — セマンティック記憶
- episodic_memory (string, required) — エピソード記憶
- created_at (timestamp, required) — 登録時刻
- metadata (object, required) — 付帯情報

**Metadata (proposed)**:

- model (string) — 解析に使用したモデル名
- message_count (integer) — 会話メッセージ数
- search_enabled (boolean) — 検索トグル状態
- top_k (integer) — 検索設定
- thread_id (string) — AG-UI のスレッドID
- client_version (string) — UI バージョン

## Entity: DiaryAnalysis

**Purpose**: Gemini から返される会話分析結果。

- title (string)
- importance_score (integer)
- summary (string)
- semantic_memory (string)
- episodic_memory (string)

## Entity: SearchSettings

**Purpose**: UI が保持する検索設定。

- enabled (boolean)
- top_k (integer, default 3)

## Entity: SearchContextItem

**Purpose**: Gemini に渡す検索コンテキスト。

- doc_id (string)
- summary (string)
- body (string)

