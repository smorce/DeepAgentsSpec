---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts in this long-running AI agent repo.
handoffs: 
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency across specs, plans, design artifacts, and tasks for this feature.
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases using tasks.md as the source of truth.
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup (feature context)**

   From the repo root, run `{SCRIPT}` and parse the JSON output.

   The script is expected to provide at least:

   * `FEATURE_SPEC`  — path to the feature spec
     (e.g. `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md`)
   * `FEATURE_DIR`   — feature directory
     (e.g. `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001`)
   * `BRANCH`        — current branch name
   * `HAS_GIT`       — `"true"` or `"false"`

   Derive:

   * `SPECS_DIR`        = `FEATURE_DIR`
   * `FEATURE_ID`       = leaf directory name of `SPECS_DIR` (typically `F-XXX-YYY`)
   * `IMPL_PLAN`        = `${SPECS_DIR}/impl-plan.md`
   * `TASKS_FILE`       = `${SPECS_DIR}/tasks.md`
   * `FEATURE_CHECKLIST`= `${SPECS_DIR}/checklists/requirements.md`
   * `PLAN_CHECKLIST`   = `${SPECS_DIR}/checklists/plan.md`
   * `EPIC_DIR`         = parent directory of the `features` directory that contains `SPECS_DIR`
     (i.e. two levels up from `SPECS_DIR`)
   * `EPIC_DESIGN_INDEX`= `${EPIC_DIR}/design/index.md`

   For single quotes in args like `"I'm Groot"`, use escape syntax: e.g. `'I'\''m Groot'`
   (or double-quote if possible: `"I'm Groot"`).

2. **Spec & Plan quality gates (required for this repo)**

   Before generating or modifying `tasks.md`, ensure that **both** spec and plan have passed their quality gates.

   1. Existence check:

      * Verify that `FEATURE_CHECKLIST` exists.
      * Verify that `PLAN_CHECKLIST` exists.

      If either is missing:

      * **STOP** and return an ERROR indicating which checklist file is missing.
      * Do **not** create or modify `TASKS_FILE`.

   2. Quality gate execution:

      From the repo root, run:

      ```bash
      scripts/validate_spec.sh "${FEATURE_CHECKLIST}" "${PLAN_CHECKLIST}"
      ```

      * If the script returns a non-zero exit code:

        * Treat this as a **quality gate failure** for this feature.

        * Do **not** create or modify `TASKS_FILE`.

        * Report:

          * The checklist paths that failed (`FEATURE_CHECKLIST`, `PLAN_CHECKLIST`).
          * The incomplete items from the validator output.

        * Prefer to append a short, timestamped entry to
          `harness/AI-Agent-progress.txt` indicating the gate failure.

      * Only if the quality gate **passes** may you proceed with the task generation workflow.

3. **Load design documents**

   From `SPECS_DIR`, load the following design artifacts:

   * **Required**:

     * `IMPL_PLAN`      — feature implementation plan
       (tech stack, libraries, project structure, milestones)
     * `FEATURE_SPEC`   — feature spec (user stories, priorities, scenarios)

   * **Optional (if present)**:

     * `research.md`    — research decisions and alternatives
     * `data-model.md`  — entities, relationships, validation rules
     * `contracts/`     — API endpoints / schemas (REST / GraphQL etc.)
     * `quickstart.md`  — how to run and test this feature in isolation

   * **Epic-level context (optional)**:

     * If `EPIC_DESIGN_INDEX` exists:

       * Read it as **cross-feature context**:

         * Shared entities and their owning features
         * Shared endpoints / routes / events
         * Cross-feature flows and sequencing
         * Any constraints that affect this feature’s scope

   Note: Not all features will have all documents yet.
   Tasks **MUST** be generated based on whatever combination is available, but:

   * `IMPL_PLAN` and `FEATURE_SPEC` are mandatory.
   * If a required document is missing, **STOP** and report which one is missing.

4. **Execute task generation workflow**

   Using the loaded documents:

   * **From `IMPL_PLAN`**:

     * Extract tech stack, primary libraries, and the **Project Structure** section.
     * Extract the key milestones / phases (setup, foundational, per-feature steps).
     * Extract any dependencies, constraints, or special safety/rollback considerations.

   * **From `FEATURE_SPEC`**:

     * Extract user stories and their priorities (P1, P2, P3, …).
     * For each story:

       * Identify the user-visible goal.
       * Identify independent test criteria (how to verify the story by itself).
       * Determine whether tests are explicitly requested (TDD / specific testing requirements).

   * **From `data-model.md` (if present)**:

     * Map entities and relationships to user stories:

       * If an entity is used in exactly one story → tasks for that entity go into that story’s phase.
       * If an entity is shared across stories → create tasks in the earliest relevant phase
         (Setup / Foundational or earliest story), and mark cross-story usage.

   * **From `contracts/` (if present)**:

     * Map contracts/endpoints to user stories:

       * Each endpoint should serve exactly one primary user story.
       * If an endpoint is shared, treat it like a shared entity:

         * Provide tasks in earliest relevant phase.
         * Mark dependent stories with integration tasks.

   * **From `research.md` (if present)**:

     * Extract decisions that imply **setup / configuration tasks**, such as:

       * Choosing a framework or library.
       * Selecting patterns (CQRS, hexagonal, etc.) that require scaffolding.
       * Security / performance constraints that need explicit tasks.

   * **From `quickstart.md` (if present)**:

     * Derive tasks that ensure the Quickstart can be followed end-to-end:

       * Commands that must exist.
       * Smoke test scenarios.
       * Any required seed data or fixtures.

   * Generate tasks organized by **phase** and **user story** (see Task Generation Rules below):

     * Phase 1: Setup (shared infrastructure)
     * Phase 2: Foundational (blocking prerequisites)
     * Phase 3+: One phase per user story (in priority order: P1, P2, P3, …)
     * Final Phase: Polish & cross-cutting concerns

   * Build a **dependency graph**:

     * Story-level: which user stories depend on which foundational elements.
     * Within a story: ordering of models → services → endpoints → integration → polish.

   * Identify and annotate **parallelizable tasks** with `[P]`:

     * Different files.
     * No dependencies on incomplete tasks.
     * Safe for a separate agent/developer.

   * Validate task completeness:

     * Each user story must have enough tasks that, once complete, the story is
       independently testable according to its criteria.
     * There must be explicit tasks to execute the Quickstart (if available).

5. **Generate `tasks.md`**

   Use `.specify/templates/tasks-template.md` as the structural template, and write the generated content to `TASKS_FILE`.

   When filling the template:

   * Set the header:

     * `Tasks: [FEATURE NAME]` where `[FEATURE NAME]` comes from:

       * Preferably the feature title from `FEATURE_SPEC`.
       * Fallback: a reasonable title derived from `FEATURE_ID` and `IMPL_PLAN`.

   * Fill **Phase 1: Setup**:

     * Tasks for project-level setup **specific to this feature** (scaffolding, configs).
     * Use paths consistent with the **Project Structure** section of `IMPL_PLAN`.

   * Fill **Phase 2: Foundational**:

     * Tasks that are hard prerequisites for all user stories.
     * No user-story-specific labels here.

   * Fill **Phase 3+ (per user story)**:

     * For each user story in priority order:

       * Title and priority (e.g. `User Story 1 - [Title] (Priority: P1)`).

       * Independent Test: concrete criteria from `FEATURE_SPEC` / `quickstart.md`.

       * Tasks grouped as:

         * (Optional) Tests — **only if explicitly requested**.
         * Models / data entities.
         * Services / domain logic.
         * Endpoints / UI / integration.
         * Story-level validation / logging / observability.

       * All tasks in these phases **must** carry `[USn]` labels.

   * Fill **Final Phase: Polish & Cross-Cutting Concerns**:

     * Tasks that touch multiple stories:

       * Docs, refactoring, performance, security hardening, extra tests, etc.
       * Validation of the Quickstart flow.

   * Include a **Dependencies & Execution Order** section:

     * Phase dependencies (Setup → Foundational → User Stories → Polish).
     * User story dependencies (which stories can be parallel, which depend on others).

   * Include **Parallel Example** and **Implementation Strategy** sections:

     * Adapt examples to actual tasks (do not leave placeholder names).

   * Ensure **ALL tasks** follow the strict checklist format (see Task Generation Rules).

6. **Report**

   At the end of the command, report:

   * `BRANCH`

   * `FEATURE_ID`

   * `TASKS_FILE` path

   * Summary:

     * Total task count
     * Task count per user story
     * Parallel opportunities identified (number of tasks marked `[P]`)
     * Independent test criteria summary per user story
     * Suggested MVP scope (typically just the highest priority story, e.g. P1 / US1)

   * Format validation result:

     * Confirm that **every** task line in `TASKS_FILE` matches:

       ```text
       - [ ] TNNN [P?] [US?] Description with file path
       ```

       or, for non-story phases (Setup, Foundational, Polish):

       ```text
       - [ ] TNNN [P?] Description with file path
       ```

   Optionally append a short, timestamped entry to `harness/AI-Agent-progress.txt`
   indicating that `tasks.md` was generated or updated for this feature.

   Context for task generation: `{ARGS}`

The `tasks.md` must be **immediately executable** — each task must be specific enough
that an LLM or novice developer can complete it without additional context beyond the
files referenced and the design artifacts in this feature directory.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature specification
or if the user requests a TDD approach in the input.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)

2. **Task ID**: Sequential number (T001, T002, T003...) in **execution order**

3. **`[P]` marker**: Include ONLY if task is parallelizable

   * Different files
   * No dependencies on incomplete tasks
   * Safe to run in parallel with other `[P]` tasks

4. **`[Story]` label**: REQUIRED for user story phase tasks only

   * Format: `[US1]`, `[US2]`, `[US3]`, etc. (maps to user stories from `FEATURE_SPEC`)
   * Setup phase: **NO** story label
   * Foundational phase: **NO** story label
   * User Story phases: **MUST** have story label
   * Polish phase: **NO** story label

5. **Description**: Clear action with **exact file path** from repo root, or from the service root if clearly implied by `IMPL_PLAN`.

**Examples**:

* ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
* ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in services/api-gateway/src/middleware/auth.ts`
* ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in services/user-service/src/models/user.ts`
* ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in services/user-service/src/services/user_service.ts`
* ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
* ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
* ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
* ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (`FEATURE_SPEC`) — PRIMARY ORGANIZATION**

   * Each user story (P1, P2, P3, …) gets its own phase (Phase 3+).

   * Map all related components to their story:

     * Models needed for that story
     * Services needed for that story
     * Endpoints / UI needed for that story
     * If tests requested: tests specific to that story

   * Mark story dependencies explicitly; most stories should be as independent as possible.

2. **From Contracts (`contracts/`)**

   * Map each contract / endpoint to the user story it primarily serves.
   * If tests requested:

     * Each contract may have a contract-test task `[P]` **before** implementation in that story’s phase.

3. **From Data Model (`data-model.md`)**

   * Map each entity to the user story(ies) that need it.
   * If an entity serves multiple stories:

     * Prefer placing creation/migration tasks in Setup / Foundational or the earliest relevant story.
     * Add integration tasks in later story phases as needed.

4. **From Setup / Infrastructure (`IMPL_PLAN`)**

   * Shared infrastructure → Setup phase (Phase 1).
   * Foundational / blocking tasks → Foundational phase (Phase 2).
   * Story-specific setup → within that story’s phase.

5. **From Epic design index (`EPIC_DESIGN_INDEX`, optional)**

   * Use this to avoid conflicting ownership of shared entities or endpoints.
   * Where cross-feature invariants exist, ensure tasks reflect those constraints
     (e.g., “do not change event shape without updating feature F-XXX-YYY”).

### Phase Structure

* **Phase 1**: Setup (project initialization; feature-specific scaffolding)

* **Phase 2**: Foundational (blocking prerequisites — MUST complete before user stories)

* **Phase 3+**: User Stories in priority order (P1, P2, P3, …)

  * Within each story:

    * (Optional) Tests (if requested)
    * Models / entities
    * Services / domain logic
    * Endpoints / UI / integration
    * Logging / observability / error handling

  * Each phase should be a complete, independently testable increment.

* **Final Phase**: Polish & Cross-Cutting Concerns

  * Docs, refactors, perf, security, cross-story cleanup, Quickstart validation.

Tasks should enable **incremental delivery**: after each user story phase, the system should have a demonstrably working, testable behavior aligned with that story.