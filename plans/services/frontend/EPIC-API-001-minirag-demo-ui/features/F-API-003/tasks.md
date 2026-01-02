# Tasks: MiniRAGデモ用チャットUI（静的HTML/JS）

**Input**: Design documents from  
`plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/`

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

- [ ] T001 Create `services/frontend/EPIC-API-001-minirag-demo-ui/public/index.html`, `public/style.css`, `public/app.js` scaffolding
- [ ] T002 Add simple dev server instructions to `services/frontend/EPIC-API-001-minirag-demo-ui/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T003 [P] Define API client helpers (base URL, headers, fetch wrapper) in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`
- [ ] T004 [P] Define basic UI state model (chat log, results list) in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - 登録→検索の体験 (Priority: P1) 🎯 MVP

**Goal**: 5件のサンプルデータを登録し、検索クエリで該当結果を表示する。

**Independent Test**: 登録ボタン→検索入力→結果表示までを単独で確認できる。

### Tests for User Story 1

- [ ] T005 [US1] Add E2E scenario for register + search in `tests/e2e/scenarios/minirag_demo_ui.spec.js`

### Implementation for User Story 1

- [ ] T006 [US1] Implement register button flow (show `registered_count`) in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`
- [ ] T007 [US1] Implement search submit flow with result rendering (top 5, note display) in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`
- [ ] T008 [US1] Render chat log and results UI in `services/frontend/EPIC-API-001-minirag-demo-ui/public/index.html`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - 削除操作の確認 (Priority: P2)

**Goal**: 任意のサンプルデータを削除し、結果から消えたことを確認できる。

**Independent Test**: 1件削除→同条件検索→削除対象が表示されないことを確認。

### Tests for User Story 2

- [ ] T009 [US2] Extend E2E scenario with delete checks in `tests/e2e/scenarios/minirag_demo_ui.spec.js`

### Implementation for User Story 2

- [ ] T010 [US2] Implement delete single/all flows in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`
- [ ] T011 [US2] Update UI to show delete results and counts in `services/frontend/EPIC-API-001-minirag-demo-ui/public/index.html`

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T012 Update `scripts/run_all_e2e_tests.sh` to include MiniRAG demo UI scenario
- [ ] T013 Add empty-input warning message rendering in `services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js`
- [ ] T014 Run `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/quickstart.md` end-to-end and update if drift exists

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
- UI flows before E2E verification.

---

## Parallel Opportunities

- T003 and T004 can run in parallel (different tasks in the same file but independent sections).
- After Foundational is complete, US1 and US2 can be developed in parallel if staffed.

---

## Parallel Example: User Story 1

```bash
Task: "T005 [US1] Add E2E scenario for register + search in tests/e2e/scenarios/minirag_demo_ui.spec.js"
Task: "T006 [US1] Implement register button flow in services/frontend/EPIC-API-001-minirag-demo-ui/public/app.js"
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
