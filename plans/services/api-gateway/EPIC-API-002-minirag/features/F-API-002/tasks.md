# Tasks: MiniRAG構造化データ登録・検索バックエンド

**Input**: Design documents from  
`plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/`

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

**Tests**: This feature explicitly includes unit and E2E tests in `impl-plan.md`.  
Tests are REQUIRED for this task list.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **`[P]`**: Can run in parallel (different files, no dependencies)
- **`[Story]`**: Which user story this task belongs to (e.g., `[US1]`, `[US2]`)
- Include **exact file paths** in descriptions (repo-root-relative or service-root-relative, consistent with `impl-plan.md`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for this feature, consistent with `impl-plan.md`.

- [ ] T001 Create module skeleton in `services/api-gateway/src/minirag/` (`schemas.py`, `repository.py`, `service.py`) and `services/api-gateway/src/routes/minirag.py`
- [ ] T002 Add MiniRAG config placeholders (DB DSN, demo API key) in `services/api-gateway/service-config.example.yaml`
- [ ] T003 [P] Add fixed 5-record sample dataset in `services/api-gateway/src/minirag/sample_data.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T004 [P] Define Pydantic schemas (StructuredDocument, SearchRequest/Response, DeleteResponse) in `services/api-gateway/src/minirag/schemas.py`
- [ ] T005 [P] Implement DB repository (upsert, search, delete) in `services/api-gateway/src/minirag/repository.py`
- [ ] T006 [P] Implement MiniRAG service layer (search note "0件", top_k default 5) in `services/api-gateway/src/minirag/service.py`
- [ ] T007 Add API key verification dependency in `services/api-gateway/src/routes/minirag.py`
- [ ] T008 Wire routes into FastAPI app in `services/api-gateway/src/app.py` (create if missing)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - サンプルデータの一括登録と検索 (Priority: P1) 🎯 MVP

**Goal**: 5件の構造化データを一括登録し、検索クエリで該当結果を返す。

**Independent Test**: 5件を登録→検索→結果に該当データが含まれることを確認。

### Tests for User Story 1

- [ ] T009 [P] [US1] Add unit tests for bulk register/search in `services/api-gateway/tests/test_minirag_routes.py`
- [ ] T010 [P] [US1] Add E2E scenario for register + search in `tests/e2e/scenarios/minirag_demo.spec.js`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `POST /minirag/documents/bulk` handler (upsert, registered_count) in `services/api-gateway/src/routes/minirag.py`
- [ ] T012 [US1] Implement `POST /minirag/search` handler (top_k default 5, note "0件") in `services/api-gateway/src/routes/minirag.py`
- [ ] T013 [US1] Load fixed sample data from `services/api-gateway/src/minirag/sample_data.py` in `services/api-gateway/src/minirag/service.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - データ削除と検索結果反映 (Priority: P2)

**Goal**: 任意データ削除と検索結果反映を確認できる。

**Independent Test**: 1件削除→同条件検索→削除対象が結果に含まれないことを確認。

### Tests for User Story 2

- [ ] T014 [P] [US2] Add unit tests for delete endpoints in `services/api-gateway/tests/test_minirag_routes.py`
- [ ] T015 [P] [US2] Extend E2E scenario with delete checks in `tests/e2e/scenarios/minirag_demo.spec.js`

### Implementation for User Story 2

- [ ] T016 [US2] Implement `DELETE /minirag/documents/{doc_id}` handler (deleted_count) in `services/api-gateway/src/routes/minirag.py`
- [ ] T017 [US2] Implement `DELETE /minirag/documents` handler (deleted_count) in `services/api-gateway/src/routes/minirag.py`
- [ ] T018 [US2] Add delete methods to `services/api-gateway/src/minirag/service.py` and `services/api-gateway/src/minirag/repository.py`

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T019 Update `scripts/run_all_unit_tests.sh` to include api-gateway MiniRAG unit tests
- [ ] T020 Update `scripts/run_all_e2e_tests.sh` to include MiniRAG demo scenario
- [ ] T021 Run `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/quickstart.md` end-to-end and update if drift exists

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational phase completion.
- **Polish (Phase 5)**: Depends on all user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational.
- **US2 (P2)**: Starts after Foundational; validates deletion against US1 data.

### Within Each User Story

- Tests should be written first and fail before implementation.
- Schemas/repository before service.
- Service before route handlers.
- Story complete and independently testable before moving to the next priority.
