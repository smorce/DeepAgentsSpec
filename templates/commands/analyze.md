---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, impl-plan.md, and tasks.md for this long-running AI agent repository.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Identify inconsistencies, duplications, ambiguities, underspecified items, and gate violations across the three core feature-level artifacts (`spec.md`, `impl-plan.md`, `tasks.md`) **before implementation**.

This command MUST run only after `/speckit.tasks` has successfully produced a complete `tasks.md`, and after:

* The **spec quality gate** (requirements checklist) has been evaluated at least once.
* The **plan quality gate** (impl-plan checklist) has been evaluated at least once.

> NOTE: This command is **read-only**. It does not fix anything; it only reports. All remediation is left to follow-up commands or manual edits.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report only. You may suggest an optional remediation plan, but the user must explicitly approve and invoke any editing commands (e.g., `/speckit.specify`, `/speckit.plan`, manual edits).

**Constitution Authority**: The project constitution (`/memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically **CRITICAL** and require adjustment of the spec, impl-plan, tasks, or checklists—not dilution, reinterpretation, or silent ignoring of the principle. If a principle itself needs to change, that must occur in a separate, explicit constitution update outside `/speckit.analyze`.

## Execution Steps

### 1. Initialize Analysis Context

Run `{SCRIPT}` once from the repository root and parse JSON for at least:

* `FEATURE_DIR` — absolute path to the feature directory
  (e.g. `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001`)
* `AVAILABLE_DOCS` — list of document basenames present in `FEATURE_DIR`
  (e.g. `["spec.md","impl-plan.md","tasks.md","research.md","data-model.md","quickstart.md"]`)

Derive absolute paths (do **not** use relative `./` or `../`):

* `SPEC`  = `${FEATURE_DIR}/spec.md`
* `PLAN`  = `${FEATURE_DIR}/impl-plan.md`
* `TASKS` = `${FEATURE_DIR}/tasks.md`

Additionally derive **quality gate checklists** for this repository:

* `SPEC_CHECKLIST` = `${FEATURE_DIR}/checklists/requirements.md`
* `PLAN_CHECKLIST` = `${FEATURE_DIR}/checklists/PlanQualityGate.md` (if present)

Abort with an error message if any **required core artifact** is missing:

* If `spec.md` missing → instruct user to run `/speckit.specify` for this feature.
* If `impl-plan.md` missing → instruct user to run `/speckit.plan` for this feature.
* If `tasks.md` missing → instruct user to run `/speckit.tasks` for this feature.

For single quotes in args like `"I'm Groot"`, use escape syntax: e.g. `'I'\''m Groot'`
(or double-quote if possible: `"I'm Groot"`).

> NOTE: Missing or incomplete checklists (`requirements.md`, `PlanQualityGate.md`) **do not abort** analysis; instead they should be reported as findings (see Detection Passes).

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From `spec.md` (feature spec):**

* Overview / Context
* Functional Requirements
* Non-Functional Requirements
* User Stories (including priorities: P1, P2, P3, etc.)
* Edge Cases (if present)
* Any `[NEEDS CLARIFICATION]` markers (should normally be absent by this stage)

**From `impl-plan.md` (feature implementation plan):**

* Architecture / stack choices
* Data model references
* Phases and milestones
* Technical constraints and assumptions
* References to design artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**From `tasks.md` (feature tasks):**

* Task IDs (T001, T002, …)
* Descriptions
* Phase grouping (Setup / Foundational / User Story phases / Polish)
* Parallel markers `[P]`
* Story labels `[US1]`, `[US2]`, …
* Referenced file paths

**From checklists (quality gates):**

* `SPEC_CHECKLIST` (`checklists/requirements.md`):

  * Any remaining unchecked items (`- [ ] ...`)
  * Line numbers and text of unmet items

* `PLAN_CHECKLIST` (`checklists/PlanQualityGate.md`, if present):

  * Any remaining unchecked items
  * Line numbers and text of unmet items

**From constitution:**

* Load `/memory/constitution.md` for principle validation:

  * Names of principles
  * MUST / SHOULD normative statements
  * Any explicit rules about specs, plans, tasks, or quality gates

### 3. Build Semantic Models

Create internal representations (do **not** include raw artifacts in output):

* **Requirements inventory**:

  * Each functional + non-functional requirement with a stable key
  * Derive a slug based on the imperative phrase; e.g.
    `"User can upload file"` → `user-can-upload-file`

* **User story / action inventory**:

  * Discrete user actions with acceptance criteria
  * Link to priority (P1, P2, P3, …)

* **Task coverage mapping**:

  * Map each task to one or more requirements or stories, using:

    * Explicit references (e.g. `[US1]`, `[US2]`)
    * Keywords / phrases from requirement slugs
    * File path hints (e.g. tasks touching `user_service.py` for user-related requirements)

* **Constitution rule set**:

  * Extract principle names and MUST / SHOULD statements
  * Note any principles explicitly about:

    * Self-containment
    * Observability / validation
    * Security / safety
    * Incremental delivery
    * Documentation / logging requirements

* **Quality gate status**:

  * For `SPEC_CHECKLIST` and `PLAN_CHECKLIST`, create:

    * A list of unmet checklist items
    * A boolean indicating whether each gate is fully satisfied

### 4. Detection Passes (Token-Efficient Analysis)

Focus on high-signal findings. Limit to **50 findings total**; aggregate the remainder in an overflow summary.

#### A. Duplication Detection

* Identify near-duplicate requirements in `spec.md`.
* Identify duplicated or overlapping tasks in `tasks.md`.
* Mark lower-quality phrasing or less precise requirement for consolidation.

#### B. Ambiguity Detection

* Flag vague adjectives and phrases without measurable criteria:

  * Examples: *fast, scalable, secure, intuitive, robust, flexible, easy to use*.
* Flag unresolved placeholders:

  * `TODO`, `TBD`, `TKTK`, `???`, `<placeholder>`, `[NEEDS CLARIFICATION]`, etc.

#### C. Underspecification

* Requirements with verbs but missing:

  * Clear object, or
  * Measurable outcome, or
  * Acceptance criterion

* User stories missing acceptance criteria alignment:

  * Story has a goal but no way to verify success.

* Tasks referencing files or components:

  * That are not mentioned in `spec.md` or `impl-plan.md`.
  * Or that appear to create new responsibilities not described in spec/plan.

#### D. Constitution Alignment

* Any requirement, plan element, or task that conflicts with a **MUST** principle:

  * Mark as **CRITICAL**.
  * Include the principle name and a short quote/summary of the rule.

* Missing mandated sections or quality gates per constitution:

  * Example: if constitution requires explicit validation steps, but `impl-plan.md` and `tasks.md` have none.

#### E. Coverage Gaps

* Requirements with **zero associated tasks**:

  * Especially P1 / P2 user stories.
  * Non-functional requirements (performance, security, observability) with no implementation or verification tasks.

* Tasks with **no mapped requirement/story**:

  * Suspicious “orphan” tasks that may reflect scope creep or outdated work.

* Non-functional requirements:

  * Security, performance, reliability, logging, monitoring.
  * Not reflected in tasks (e.g. no performance test, no security hardening tasks).

#### F. Inconsistency

* Terminology drift:

  * Same concept named differently across files (`user`, `account`, `member`, etc.).

* Data entities:

  * Referenced in `impl-plan.md` but absent in `spec.md`, or vice versa.

* Task ordering contradictions:

  * Example: integration tasks before foundational setup tasks without any dependency note or prior step.

* Conflicting requirements:

  * Example: spec requires `Next.js` while `impl-plan.md` specifies `Vue`.
  * Example: tasks implement a synchronous API where spec calls for async behavior.

#### G. Quality Gate Status (Project-Specific)

For this repository, explicitly evaluate **spec** and **plan** quality gates:

* From `SPEC_CHECKLIST` (`checklists/requirements.md`):

  * If any unchecked items remain, create a finding:

    * Severity at least **HIGH**, **CRITICAL** if they block core P1 behavior.
    * Summarize which checklist lines are still open.

* From `PLAN_CHECKLIST` (`checklists/PlanQualityGate.md`, if present):

  * If any unchecked items remain, create a finding:

    * Severity at least **HIGH**, **CRITICAL** if they break constitution or make execution unsafe.
    * Summarize open items (for example: missing validation strategy, missing rollback instructions).

> NOTE: Do **not** modify checklists. Only read them and surface their current status.

### 5. Severity Assignment

Use this heuristic to prioritize findings:

* **CRITICAL**:

  * Violates a constitution **MUST**.
  * Missing core spec/plan artifact (spec, impl-plan, tasks).
  * Requirement with zero coverage that blocks baseline P1 functionality.
  * Spec/plan quality gate failure for P1 behavior.

* **HIGH**:

  * Duplicate or conflicting requirement for core flows.
  * Ambiguous security or performance attributes.
  * Untestable acceptance criteria for P1/P2 user stories.
  * Serious checklist gaps that risk incorrect implementation.

* **MEDIUM**:

  * Terminology drift.
  * Missing non-functional task coverage (but not catastrophic).
  * Underspecified edge cases.
  * Incomplete documentation for secondary flows.

* **LOW**:

  * Style/wording improvements.
  * Minor redundancy not affecting execution order.
  * Cosmetic inconsistencies.

### 6. Produce Compact Analysis Report

Output a Markdown report (no file writes) with the following structure:

```markdown
## Specification Analysis Report

| ID | Category    | Severity | Location(s)             | Summary                                | Recommendation                        |
|----|-------------|----------|-------------------------|----------------------------------------|----------------------------------------|
| A1 | Duplication | HIGH     | spec.md:L120-134        | Two similar requirements ...           | Merge phrasing; keep clearer version   |
| C3 | Coverage    | CRITICAL | spec.md §User Stories   | Story 'user-can-signup' has no tasks   | Add tasks in tasks.md for this story   |
| G1 | Gate        | HIGH     | checklists/PlanQualityGate.md      | Plan checklist has 3 open items        | Resolve checklist then rerun analyze   |
```

(Add one row per finding; generate stable IDs prefixed by category initial: A/B/C/D/E/F/G.)

Then add a **Coverage Summary Table**:

```markdown
### Coverage Summary

| Requirement Key           | Has Task? | Task IDs         | Notes                             |
|---------------------------|-----------|------------------|-----------------------------------|
| user-can-signup           | Yes       | T012, T015       | Covered via US1 implementation    |
| user-gets-verification    | No        | —                | Missing tasks for email flow      |
| performance-p95-under-200 | Partial   | T090             | No explicit validation step       |
```

Include, if applicable:

* **Constitution Alignment Issues:** (list IDs of CRITICAL findings referencing the constitution)
* **Unmapped Tasks:** (tasks that could not be mapped to any requirement/story)

**Metrics:**

* Total Requirements
* Total User Stories
* Total Tasks
* Coverage % (requirements with ≥1 mapped task)
* Ambiguity Count
* Duplication Count
* Critical Issues Count

### 7. Provide Next Actions

At the end of the report, output a concise **Next Actions** block, for example:

```markdown
### Next Actions

- CRITICAL issues detected → Do **not** run `/speckit.implement` yet.
- Recommended order of remediation:
  1. Fix constitution violations and gate failures in spec/impl-plan/tasks.
  2. Add missing tasks for uncovered P1 requirements.
  3. Resolve high-severity ambiguities (especially around security/performance).
- Suggested commands / follow-ups:
  - Refine spec: run `/speckit.specify` with updated requirements, then re-validate `checklists/requirements.md`.
  - Adjust implementation plan: run `/speckit.plan` to update `impl-plan.md` and `checklists/PlanQualityGate.md`.
  - Update tasks: rerun `/speckit.tasks` or manually edit `tasks.md` to add coverage for uncovered requirements.
```

If only LOW / MEDIUM issues exist:

* State that the user **may proceed** to `/speckit.implement`, but highlight recommended improvements.

### 8. Offer Remediation

Conclude with an explicit remediation offer (without making changes):

```markdown
Would you like me to suggest concrete remediation edits for the top N issues (starting from CRITICAL, then HIGH)?
Note: I will only propose edits; you or a separate command must apply them.
```

Do **not** apply changes automatically.

## Operating Principles

### Context Efficiency

* **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation.
* **Progressive disclosure**: Load artifacts incrementally; do not dump entire files into the analysis context if not needed.
* **Token-efficient output**: Limit detailed findings table to at most 50 rows; summarize overflow with counts and categories.
* **Deterministic results**: Rerunning without file changes should produce consistent IDs, counts, and severities.

### Analysis Guidelines

* **NEVER modify files** (this is a read-only analysis step).
* **NEVER hallucinate missing sections** (if a section is absent, report it as missing instead of assuming content).
* **Prioritize constitution violations and gate failures** (these are always CRITICAL or HIGH).
* **Use concrete examples** over generic statements (point to specific sections/lines).
* **Report zero issues gracefully**:

  * If no issues found, emit a success report with coverage statistics and an explicit “no CRITICAL/HIGH issues detected” statement.

## Context

{ARGS}