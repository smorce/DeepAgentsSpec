---
description: "Task list template for feature implementation in this long-running AI agent repo"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from  
`plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/`

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

## Path Conventions

This repository uses `plans/` + `services/` layout with service-specific code trees.  
The **authoritative structure** is defined in the `Project Structure` section of `impl-plan.md`.

Typical patterns (examples — adjust to this feature’s `impl-plan.md`):

- `services/<service-name>/src/...`        — main service code
- `services/<service-name>/tests/...`      — tests for that service
- `tests/e2e/...`                          — cross-service E2E tests
- `docs/...`                               — user / operator documentation

> `/speckit.tasks` MUST replace the sample tasks below with actual tasks for this feature,  
> based on:
>
> - User stories from `spec.md` (with their priorities P1, P2, P3, …)
> - Implementation details and structure from `impl-plan.md`
> - Entities from `data-model.md`
> - Contracts from `contracts/`
> - Scenarios from `quickstart.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for this feature, consistent with `impl-plan.md`.

<!-- Replace the examples below with real tasks -->

- [ ] T001 Create feature-specific directories per implementation plan (e.g. services/user-service/src/...).
- [ ] T002 Initialize configuration for this feature (e.g. env vars, feature flags).
- [ ] T003 [P] Ensure linting/formatting tools are configured for files touched by this feature.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

Examples of foundational tasks (adjust based on your project and `impl-plan.md`):

- [ ] T004 Setup or extend database schema/migrations for this feature in services/<service>/migrations/.
- [ ] T005 [P] Implement shared middleware/infrastructure (e.g. auth, routing) referenced by multiple stories.
- [ ] T006 [P] Add base domain models/entities shared across user stories in services/<service>/src/models/.
- [ ] T007 Configure logging and error handling that all stories will rely on.
- [ ] T008 Wire up any shared configuration or dependency injection needed by services in this feature.

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own — from spec.md / quickstart.md]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [ ] T010 [P] [US1] Contract test for [endpoint] in services/<service>/tests/contract/test_[name].ts
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/e2e/test_[name].ts

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Entity1] model in services/<service>/src/models/[entity1].ts
- [ ] T013 [P] [US1] Create [Entity2] model in services/<service>/src/models/[entity2].ts
- [ ] T014 [US1] Implement [Service] in services/<service>/src/services/[service].ts (depends on T012, T013)
- [ ] T015 [US1] Implement [endpoint/feature] handler in services/<service>/src/handlers/[file].ts
- [ ] T016 [US1] Add validation and error handling for User Story 1 flows.
- [ ] T017 [US1] Add logging/metrics for User Story 1 operations.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint] in services/<service>/tests/contract/test_[name].ts
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/e2e/test_[name].ts

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create or extend [Entity] model in services/<service>/src/models/[entity].ts
- [ ] T021 [US2] Implement [Service] in services/<service>/src/services/[service].ts
- [ ] T022 [US2] Implement [endpoint/feature] in services/<service>/src/handlers/[file].ts
- [ ] T023 [US2] Integrate with User Story 1 components (if needed) without breaking US1’s independent tests.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint] in services/<service>/tests/contract/test_[name].ts
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/e2e/test_[name].ts

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create or extend [Entity] model in services/<service>/src/models/[entity].ts
- [ ] T027 [US3] Implement [Service] in services/<service>/src/services/[service].ts
- [ ] T028 [US3] Implement [endpoint/feature] in services/<service>/src/handlers/[file].ts

**Checkpoint**: All user stories should now be independently functional.

---

[Add more user story phases as needed, following the same pattern.]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] TXXX [P] Documentation updates for this feature in docs/<area>/.
- [ ] TXXX Code cleanup and refactoring across services touched by this feature.
- [ ] TXXX Performance optimization across all stories (e.g., DB indices, caching).
- [ ] TXXX [P] Additional unit tests (if requested) in services/<service>/tests/unit/.
- [ ] TXXX Security hardening (e.g., rate-limiting, input sanitization).
- [ ] TXXX Run and validate `quickstart.md` flow end-to-end.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.

  * User stories can then proceed in parallel (if staffed).
  * Or sequentially in priority order (P1 → P2 → P3).

- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — ideally no dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — may integrate with US1 but should be independently testable.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — may integrate with US1/US2 but should be independently testable.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before cross-story integration.
- Story complete and independently testable before moving to the next priority.

### Parallel Opportunities

- All Setup tasks marked `[P]` can run in parallel.
- All Foundational tasks marked `[P]` can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked `[P]` can run in parallel.
- Models within a story marked `[P]` can run in parallel.
- Different user stories can be worked on in parallel by different team members or agents.

---

## Parallel Example: User Story 1

```bash
# Example: launch tasks for User Story 1 in parallel (conceptual):

Task: "T012 [P] [US1] Create User model in services/user-service/src/models/user.ts"
Task: "T013 [P] [US1] Create Profile model in services/user-service/src/models/profile.ts"

# If tests are requested:

Task: "T010 [P] [US1] Contract test for POST /signup in services/user-service/tests/contract/test_signup.ts"
Task: "T011 [P] [US1] Integration test for basic signup flow in tests/e2e/test_signup_flow.ts"
````

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: User Story 1 (P1).
4. **STOP and VALIDATE**: Test User Story 1 independently using the criteria and Quickstart instructions.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready.
2. Add User Story 1 → test independently → deploy/demo (MVP).
3. Add User Story 2 → test independently → deploy/demo.
4. Add User Story 3 → test independently → deploy/demo.
5. Each story adds value without breaking previous stories.

### Parallel Team / Agent Strategy

With multiple developers or agents:

1. Team completes Setup + Foundational together.

2. Once Foundational is done:

   * Developer/Agent A: User Story 1
   * Developer/Agent B: User Story 2
   * Developer/Agent C: User Story 3

3. Stories complete and integrate independently.

---

## Notes

* `[P]` tasks = different files, no dependencies; safe to execute in parallel.
* `[USn]` labels map tasks to specific user stories for traceability.
* Each user story should be independently completable and testable.
* Verify tests fail before implementing (when tests are included).
* Commit after each task or logical group of tasks.
* You should be able to **stop at any checkpoint** and still have a working,
  demonstrably useful increment aligned with at least one user story.
* Avoid vague tasks, multiple writers modifying the same file simultaneously,
  and cross-story dependencies that break story independence.
