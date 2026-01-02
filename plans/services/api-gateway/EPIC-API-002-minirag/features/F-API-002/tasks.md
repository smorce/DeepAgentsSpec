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

**Tests**: The examples below include test tasks.  
Tests are OPTIONAL — include them **only** if explicitly requested in the feature specification or by the user.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **`[P]`**: Can run in parallel (different files, no dependencies)
- **`[Story]`**: Which user story this task belongs to (e.g., `[US1]`, `[US2]`, `[US3]`)
- Include **exact file paths** in descriptions (repo-root-relative or service-root-relative, consistent with `impl-plan.md`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for this feature, consistent with `impl-plan.md`.

- [ ] T001 Create `services/api-gateway/src/minirag/__init__.py`, `schemas.py`, `repository.py`, `service.py` and `services/api-gateway/src/routes/minirag.py` scaffolding
- [ ] T002 Create `services/api-gateway/src/main.py` (FastAPI app entrypoint) and register the MiniRAG router from `services/api-gateway/src/routes/minirag.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T003 [P] Define Pydantic schemas for StructuredDocument/SearchRequest/SearchResponse/DeleteResponse in `services/api-gateway/src/minirag/schemas.py`
- [ ] T004 [P] Implement MiniRAG repository (upsert/search/delete) in `services/api-gateway/src/minirag/repository.py`
- [ ] T005 Implement service layer orchestration (register/search/delete, 0件注記, 削除件数) in `services/api-gateway/src/minirag/service.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - サンプルデータの一括登録と検索 (Priority: P1) 🎯 MVP

**Goal**: 5件のサンプルデータを一括登録し、検索クエリで該当結果を返す。

**Independent Test**: 5件を登録→検索クエリを実行→検索結果に該当データが含まれることを確認。

### Tests for User Story 1

- [ ] T006 [US1] Add unit tests for bulk register + search in `services/api-gateway/tests/test_minirag_routes.py`
- [ ] T007 [US1] Add E2E scenario for register + search in `tests/e2e/scenarios/minirag_demo.spec.js`

### Implementation for User Story 1

- [ ] T008 [US1] Implement bulk register endpoint with API key check in `services/api-gateway/src/routes/minirag.py`
- [ ] T009 [US1] Implement search endpoint (0件は空配列+注記) in `services/api-gateway/src/routes/minirag.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - データ削除と検索結果反映 (Priority: P2)

**Goal**: 任意のサンプルデータを削除し、検索結果から消えることを確認できる。

**Independent Test**: 1件削除→同条件検索→削除対象が結果に含まれないことを確認。

### Tests for User Story 2

- [ ] T010 [US2] Add unit tests for delete single/all + deleted_count in `services/api-gateway/tests/test_minirag_routes.py`
- [ ] T011 [US2] Extend E2E scenario with delete checks in `tests/e2e/scenarios/minirag_demo.spec.js`

### Implementation for User Story 2

- [ ] T012 [US2] Implement delete single endpoint returning deleted_count in `services/api-gateway/src/routes/minirag.py`
- [ ] T013 [US2] Implement delete all endpoint returning deleted_count in `services/api-gateway/src/routes/minirag.py`

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T014 Update `scripts/run_all_unit_tests.sh` to include api-gateway unit tests
- [ ] T015 Update `scripts/run_all_e2e_tests.sh` to include MiniRAG E2E scenario
- [ ] T016 Run `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/quickstart.md` end-to-end and update if drift exists

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

- Tests (if included) should be written first and fail before implementation.
- Schemas → repository/service → endpoints → E2E verification.

---

## Parallel Opportunities

- T003 and T004 can run in parallel (different files).
- After Foundational is complete, US1 and US2 can be developed in parallel if staffed.

---

## Parallel Example: User Story 1

```bash
Task: "T006 [US1] Add unit tests for bulk register + search in services/api-gateway/tests/test_minirag_routes.py"
Task: "T008 [US1] Implement bulk register endpoint with API key check in services/api-gateway/src/routes/minirag.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. STOP and validate User Story 1 with its independent test criteria.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add User Story 1 → test independently → demo.
3. Add User Story 2 → test independently → demo.
4. Polish phase → validate scripts and quickstart.

---

## Notes

* `[USn]` labels map tasks to specific user stories for traceability.
* Each user story should be independently completable and testable.
* Avoid cross-story dependencies that break story independence.
