# Tasks: 日記会話の構造化登録とMiniRAG検索連携

**Input**: Design documents from  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/`

**Prerequisites** (for generating this file):

- `spec.md` (feature spec with user stories and priorities)
- `impl-plan.md` (feature implementation plan)
- `checklists/requirements.md` (spec quality checklist — PASSED via `scripts/validate_spec.sh`)
- `checklists/PlanQualityGate.md` (plan quality checklist — PASSED via `scripts/validate_plan.sh`)

**Optional but recommended design artifacts**:

- `research.md` (decisions and rationale)
- `data-model.md` (entities, relationships, validations)
- `contracts/` (API / event contracts)
- `quickstart.md` (how to run and test this feature)

**Tests**: Tests are OPTIONAL — none are required explicitly in the feature spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **`[P]`**: Can run in parallel (different files, no dependencies)
- **`[Story]`**: Which user story this task belongs to (e.g., `[US1]`, `[US2]`)
- Include **exact file paths** in descriptions (repo-root-relative or service-root-relative, consistent with `impl-plan.md`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for this feature, consistent with `impl-plan.md`.

- [ ] T001 Create server scaffolding files in `services/avatar-ui/server/src/minirag_client.py`, `services/avatar-ui/server/src/diary_service.py`, `services/avatar-ui/server/src/routes/diary.py`.
- [ ] T002 Add MiniRAG + diary settings to `services/avatar-ui/server/src/config.py` and `services/avatar-ui/settings.json5` (workspace `diary`, top_k default 3, search toggle default).
- [ ] T003 [P] Add UI control placeholders in `services/avatar-ui/app/src/renderer/index.html` and base styles in `services/avatar-ui/app/src/renderer/style.css` for search toggle, top_k, and finalize button.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T004 Implement MiniRAG HTTP client (`bulk_insert`, `search`) in `services/avatar-ui/server/src/minirag_client.py` with workspace `diary` support.
- [ ] T005 Implement in-memory search settings store and transcript helpers in `services/avatar-ui/server/src/diary_service.py` (per-thread settings: enabled/top_k).
- [ ] T006 Wire diary router into `services/avatar-ui/server/main.py` and ensure CORS covers UI origin.

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - 会話確定による日記登録 (Priority: P1) 🎯 MVP

**Goal**: 会話確定ボタンで Gemini が重要度/サマリー/記憶を生成し、MiniRAG に登録できる。

**Independent Test**: 会話 → 会話確定 → 登録結果（doc_id と重要度）が UI に表示される。

### Implementation for User Story 1

- [ ] T007 [P] [US1] Define request/response models for `/agui/diary/finalize` in `services/avatar-ui/server/src/routes/diary.py` (messages, thread_id, search_settings).
- [ ] T008 [P] [US1] Implement Gemini analysis prompt + JSON parsing in `services/avatar-ui/server/src/diary_service.py` (title, importance_score, summary, semantic_memory, episodic_memory).
- [ ] T009 [US1] Build MiniRAG document mapping in `services/avatar-ui/server/src/diary_service.py` (doc_id format, body composition, metadata fields).
- [ ] T010 [US1] Implement `/agui/diary/finalize` handler in `services/avatar-ui/server/src/routes/diary.py` calling `minirag_client.bulk_insert` and returning analysis + doc_id.
- [ ] T011 [P] [US1] Capture transcript (user/assistant messages) and hook finalize button in `services/avatar-ui/app/src/renderer/main.ts` to POST `/agui/diary/finalize`.
- [ ] T012 [US1] Render finalize result output in `services/avatar-ui/app/src/renderer/main.ts` (importance score + summary) and show errors in UI.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - 会話中の過去日記検索 (Priority: P2)

**Goal**: Gemini が必要時に MiniRAG 検索を実行し、doc_id/summary/body の上位N件を文脈として使える。

**Independent Test**: 検索トグル ON で過去日記質問時に検索が走り、OFF では検索しない。

### Implementation for User Story 2

- [ ] T013 [US2] Implement `/agui/diary/search-settings` endpoint in `services/avatar-ui/server/src/routes/diary.py` to store enabled/top_k per thread.
- [ ] T014 [US2] Add MiniRAG search tool in `services/avatar-ui/server/main.py` that uses user input text as query, respects toggle/top_k, and returns doc_id/summary/body only.
- [ ] T015 [US2] Update system prompt or tool description in `services/avatar-ui/settings.json5` to instruct Gemini on when to call the search tool.
- [ ] T016 [US2] Implement UI toggle + top_k handling in `services/avatar-ui/app/src/renderer/main.ts` to POST `/agui/diary/search-settings`.

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T017 Update documentation in `services/avatar-ui/README.ja.md` to include diary flow usage and new settings.
- [ ] T018 Run and validate `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/quickstart.md` end-to-end and update if drift exists.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependency on other stories.
- **User Story 2 (P2)**: Can start after Foundational — depends on shared MiniRAG client and settings store.

### Within Each User Story

- Models/helpers before services.
- Services before endpoints.
- Core implementation before UI integration.
- Story complete and independently testable before moving to the next priority.

---

## Parallel Example: User Story 1

Task: "T007 [P] [US1] Define request/response models for `/agui/diary/finalize` in services/avatar-ui/server/src/routes/diary.py"  
Task: "T008 [P] [US1] Implement Gemini analysis prompt + JSON parsing in services/avatar-ui/server/src/diary_service.py"

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. STOP and validate User Story 1 with its independent test criteria.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → validate finalize flow.
3. Add User Story 2 → validate search toggle + tool usage.
4. Polish phase → validate Quickstart.

