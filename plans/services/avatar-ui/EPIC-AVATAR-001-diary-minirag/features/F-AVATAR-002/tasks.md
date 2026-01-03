# Tasks: 日記会話のプロファイリング更新

**Input**: Design documents from  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/`

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

**Tests**: Tests are OPTIONAL — unit tests are recommended for profile merge logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **`[P]`**: Can run in parallel (different files, no dependencies)
- **`[Story]`**: Which user story this task belongs to (e.g., `[US1]`, `[US2]`)
- Include **exact file paths** in descriptions (repo-root-relative or service-root-relative, consistent with `impl-plan.md`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for this feature, consistent with `impl-plan.md`.

- [ ] T001 Create profiling scaffolding files in `services/avatar-ui/server/src/profile_store.py` and `services/avatar-ui/server/src/profile_service.py`.
- [ ] T002 [P] Add profiling settings to `services/avatar-ui/server/src/config.py` and `services/avatar-ui/settings.json5` (model, confidence threshold).
- [ ] T003 [P] Add profiling contract to `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/contracts/profile-update.schema.json`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [ ] T004 Implement YAML read/write and path validation in `services/avatar-ui/server/src/profile_store.py` using the default profile as a schema source.
- [ ] T005 Implement profile update application (non-empty overwrite guard, confidence threshold) in `services/avatar-ui/server/src/profile_service.py`.

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - 会話確定時にプロフィールが更新される (Priority: P1) 🎯 MVP

**Goal**: 会話確定後にユーザー発話のみを分析し、プロファイルが差分更新される。

**Independent Test**: 会話 → 会話確定 → プロファイル更新が行われる。

### Implementation for User Story 1

- [ ] T006 [US1] Extract user-only transcript in `services/avatar-ui/server/src/diary_service.py` and pass to profiling flow after MiniRAG registration success.
- [ ] T007 [US1] Call profiling update and attach `profiling` status to `/agui/diary/finalize` response in `services/avatar-ui/server/src/routes/diary.py`.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - プロファイリング失敗時に通知される (Priority: P1)

**Goal**: profiling 失敗時に UI が警告表示し、日記登録の成功/失敗とは独立して扱われる。

**Independent Test**: profiling の失敗を発生させ、UI に警告表示が出る。

### Implementation for User Story 2

- [ ] T008 [US2] Render profiling failure message in `services/avatar-ui/app/src/renderer/main.ts` based on finalize response.
- [ ] T009 [US2] Add warning style in `services/avatar-ui/app/src/renderer/style.css` if needed.

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: Tests & Docs

**Purpose**: Quality and documentation updates for maintainability.

- [ ] T010 Add unit tests for merge rules in `services/avatar-ui/server/tests/test_profile_merge.py`.
- [ ] T011 Update `services/avatar-ui/README.ja.md` with profiling update behavior and failure notification.
- [ ] T012 Run and validate `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/quickstart.md` end-to-end and update if drift exists.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational phase completion.
- **Tests & Docs (Final Phase)**: Depends on desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependency on other stories.
- **User Story 2 (P1)**: Can start after User Story 1 — depends on response payload.

### Within Each User Story

- Services before endpoints.
- Endpoints before UI integration.
- Story complete and independently testable before moving to the next priority.
