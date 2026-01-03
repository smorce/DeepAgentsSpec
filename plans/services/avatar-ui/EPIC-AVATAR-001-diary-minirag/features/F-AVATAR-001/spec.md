# Feature Specification: 日記会話の構造化登録とMiniRAG検索連携

**Feature ID**: F-AVATAR-001  
**Feature Branch**: `F-AVATAR-001-diary-minirag`  
**Created**: 2026-01-03  
**Status**: Draft  
**Input**: User description: "Gemini と会話しつつ日記を構造化して MiniRAG に登録し、必要時に過去日記を検索してコンテキストだけを Gemini に渡したい"  
**Spec Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md` (validate via `scripts/validate_spec.sh`)

## Overview & Goal *(mandatory)*

ユーザーは avatar-ui 上で Gemini と日記会話を行い、会話終了時にボタンで「会話確定」を行うことで、その日の出来事を構造化データとして MiniRAG に保存できる。会話中、Gemini は必要と判断した場合のみ MiniRAG 検索を使い、過去日記の要約・本文・doc_id を文脈として受け取り、会話を継続できる。

## Scope & Out of Scope *(mandatory)*

### In Scope

- 会話確定ボタンによる日記登録フロー
- Gemini による重要度評価（1-10）と日記サマリー生成
- セマンティック記憶・エピソード記憶の抽出
- MiniRAG 登録用の構造化データ生成と登録
- MiniRAG 検索コンテキスト（doc_id / summary / body）の取得
- 検索 ON/OFF トグルと top_k 設定

### Out of Scope

- MiniRAG API 側の変更
- 複数ユーザーや認証機能
- 日記の編集・削除・公開機能
- 音声入力や音声合成の改善

---

## Reference Materials *(mandatory to cite actual docs)*

- `architecture/system-architecture.md`
- `architecture/service-boundaries.md`
- `architecture/deployment-topology.md`
- `services/avatar-ui/service-architecture.md`
- `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`
- `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 会話確定による日記登録 (Priority: P1)

利用者は、Gemini と会話した内容をボタン操作で確定し、重要度・サマリー・記憶情報を含む日記として MiniRAG に保存できる。

**Why this priority**: 日記の構造化保存が主目的であり、確実に保存できることが最優先だから。

**Independent Test**: 会話 → ボタン確定 → MiniRAG 登録成功が単独で確認できる。

**Acceptance Scenarios**:

1. **Given** 会話履歴がある状態、**When** 会話確定ボタンを押す、**Then** 重要度・サマリー・記憶が生成され、MiniRAG 登録結果が表示される
2. **Given** 会話履歴がない状態、**When** 会話確定ボタンを押す、**Then** 登録は行われず、理由が表示される

---

### User Story 2 - 会話中の過去日記検索 (Priority: P2)

利用者が過去日記に関する質問をした場合、Gemini は必要に応じて MiniRAG 検索を行い、コンテキストだけを受け取り会話を継続できる。

**Why this priority**: 過去日記を参照した会話継続が付加価値になるため。

**Independent Test**: 検索トグルを ON にし、過去日記を想起する質問で検索が実行されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 検索トグル ON、**When** 過去日記に関する質問をする、**Then** MiniRAG 検索が行われ、Gemini に文脈が渡される
2. **Given** 検索トグル OFF、**When** 同じ質問をする、**Then** 検索は行われず、Gemini は自前の会話のみで応答する

---

### Edge Cases *(mandatory)*

- トグル OFF の状態で検索が要求されても結果を返さない
- MiniRAG が一時的に利用不可な場合、検索結果は空として扱い会話を継続する
- Gemini の分析結果が想定 JSON 形式で返らない場合、再試行またはエラー表示を行う
- 会話履歴が極端に長い場合はサマリーを優先し、全文は制限付きで保存する

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: UI は会話確定ボタンを提供し、押下で会話確定フローを開始できなければならない
- **FR-002**: UI は検索 ON/OFF トグルと top_k 設定を提供し、ユーザーが制御できなければならない
- **FR-003**: 会話確定時に Gemini が重要度（1-10）を付与しなければならない
- **FR-004**: 会話確定時に Gemini が日記サマリー、セマンティック記憶、エピソード記憶を生成しなければならない
- **FR-005**: サーバーは MiniRAG に構造化データを登録し、登録結果を UI に返さなければならない
- **FR-006**: Gemini が必要と判断した場合のみ MiniRAG 検索を実行し、上位N件の doc_id / summary / body を渡さなければならない
- **FR-007**: 検索トグル OFF の場合は検索を実行してはならない

### Non-Functional Requirements *(include if relevant)*

- **NFR-001**: 会話確定操作の結果はユーザーが理解できる形で表示される
- **NFR-002**: 検索結果が0件の場合でも会話が破綻しない
- **NFR-003**: workspace は固定値 `diary` を使用する

### Key Entities *(include if feature involves data)*

- **DiaryEntry**: workspace, doc_id, title, summary, body, importance_score, semantic_memory, episodic_memory, metadata
- **DiaryAnalysis**: important_score, summary, semantic_memory, episodic_memory
- **SearchContext**: doc_id, summary, body

---

## Assumptions *(mandatory to review; keep short but explicit)*

- workspace は固定で `diary`
- 会話確定はユーザーのボタン操作で行う
- MiniRAG 検索の top_k デフォルトは 3
- MiniRAG API は既存のエンドポイントを利用する

---

## Dependencies & Constraints *(include if relevant)*

- **Dependencies**:
  - F-API-002（MiniRAG API）

- **Constraints**:
  - 実装対象は avatar-ui のみ
  - Gemini との会話は既存の AG-UI サーバー経由で行う

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 会話確定ボタン操作で MiniRAG に登録できる（1回以上成功）
- **SC-002**: 検索トグル ON/OFF が UI 上で明確に操作できる
- **SC-003**: 検索 ON 時にのみコンテキストが Gemini に渡される

---

## Checklist & Gate Integration

- Mirror updates from this spec into `checklists/requirements.md` under the same
  feature directory and run `scripts/validate_spec.sh <path-to-requirements.md>`
  until it reports `PASSED`.
- Record spec validation results in `harness/AI-Agent-progress.txt` per project rules.

