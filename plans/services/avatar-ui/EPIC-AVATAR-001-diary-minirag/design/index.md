# Epic Design Index: EPIC-AVATAR-001-DIARY-MINIRAG

## 1. Scope & Owner

- ExecPlan: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`
- Scope:
  - Service: avatar-ui
  - Primary dependencies: api-gateway (MiniRAG API)
- Summary:
  - Gemini 会話を日記として構造化し、MiniRAG に登録・検索する。

## 2. Feature Map

- F-AVATAR-001: 日記会話の構造化登録とMiniRAG検索連携
  - Spec: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`
  - Impl plan: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/impl-plan.md`
  - Data model: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/data-model.md`
  - Contracts: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/contracts/`
  - Quickstart: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/quickstart.md`
- F-AVATAR-002: 日記会話のプロファイリング更新
  - Spec: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/spec.md`
  - Impl plan: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/impl-plan.md`
  - Data model: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/data-model.md`
  - Contracts: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/contracts/`
  - Quickstart: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/quickstart.md`

## 3. Shared Entities & Ownership

- DiaryEntry
  - Owner: F-AVATAR-001
  - Notes: MiniRAG の StructuredDocument にマッピング

- DiarySearchContext
  - Owner: F-AVATAR-001
  - Notes: Gemini へ渡す doc_id / summary / body の上位N件

- UserProfile
  - Owner: F-AVATAR-002
  - Notes: 固定項目のユーザープロファイル（YAML）

- ProfileUpdate
  - Owner: F-AVATAR-002
  - Notes: Gemini が生成する差分更新（path/value/confidence）

## 4. Shared APIs / Contracts

- MiniRAG bulk insert
  - Owner feature: F-AVATAR-001
  - Endpoint: `POST /minirag/documents/bulk`
  - Consumer: avatar-ui server

- MiniRAG search
  - Owner feature: F-AVATAR-001
  - Endpoint: `POST /minirag/search`
  - Consumer: Gemini tool (avatar-ui server)

- Diary finalize
  - Owner feature: F-AVATAR-001
  - Endpoint: `POST /agui/diary/finalize`
  - Consumer: avatar-ui UI
  - Notes: F-AVATAR-002 で profiling status をレスポンスに追加

- Search settings toggle
  - Owner feature: F-AVATAR-001
  - Endpoint: `POST /agui/diary/search-settings`
  - Consumer: avatar-ui UI

- Profile update contract
  - Owner feature: F-AVATAR-002
  - Contract: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/contracts/profile-update.schema.json`

## 5. Cross-Feature Flows

### 会話確定 → 構造化登録

1. ユーザーが UI の「会話確定」ボタンを押す。
2. UI がトランスクリプトと設定を server に送信する。
3. server が Gemini に分析を依頼し、重要度・サマリー・記憶を生成する。
4. server が MiniRAG に構造化データを登録する。
5. UI に登録結果を返す。

### 会話中の検索補助

1. Gemini が必要に応じて検索ツールを呼び出す。
2. server が MiniRAG へ検索し、上位N件の doc_id / summary / body を返す。
3. Gemini がコンテキストとして利用し、会話を継続する。

### 会話確定 → プロファイル更新

1. 日記登録が成功する。
2. server がユーザー発話のみを分析し、プロファイル差分を生成する。
3. 既存値を保護しつつプロファイルを更新する。
4. UI に profiling の成功/失敗を通知する。
