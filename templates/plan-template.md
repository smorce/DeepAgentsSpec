# Implementation Plan: [FEATURE_ID]

**Branch**: `[###-feature-branch]` | **Date**: [DATE]  
**Epic**: `[EPIC-ID]` (`plans/<scope>/<service-or-system>/<EPIC-ID>/exec-plan.md`)  
**Feature Spec**: `[relative path to spec.md]`  
**Spec Checklist**: `[relative path to checklists/requirements.md]`  

**Input**: Feature specification under  
`plans/<scope>/<service-or-system>/<EPIC-ID>/features/[FEATURE_ID]/spec.md`  
with a passing spec quality checklist at  
`plans/<scope>/<service-or-system>/<EPIC-ID>/features/[FEATURE_ID]/checklists/requirements.md`.

**Note**:  
This file is created and updated by the `/speckit.plan` command, which uses:

- `scripts/bash/setup-plan.sh --json` or  
- `scripts/powershell/setup-plan.ps1 -Json`

to determine:

- `FEATURE_SPEC` (spec.md)
- `IMPL_PLAN` (this file)
- `SPECS_DIR` (feature directory)
- `BRANCH`

The execution workflow for `/speckit.plan` is defined in  
`templates/commands/plan.md`.

---

## Summary

[Extract from feature spec: primary requirement, success criteria, and a short technical approach derived from research.md]

---

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the concrete
  technical details for this feature in THIS REPOSITORY.

  Use the feature spec, the epic’s exec-plan.md, and (if present)
  plans/<...>/<EPIC-ID>/design/index.md as primary inputs.

  Unknowns should be explicitly marked as "NEEDS CLARIFICATION" so that
  Phase 0 research tasks can resolve them.
-->

**Language/Version**: [e.g., TypeScript 5.x, Go 1.22, Python 3.11 or NEEDS CLARIFICATION]  
**Primary Services**: [e.g., api-gateway, user-service, billing-service or NEEDS CLARIFICATION]  
**Primary Dependencies**: [frameworks/libs used in services/, or NEEDS CLARIFICATION]  
**Storage**: [e.g., PostgreSQL, Redis, files, external APIs or N/A]  
**Testing**: [e.g., Jest, pytest, Go test, e2e runner or NEEDS CLARIFICATION]  
**Target Environment**: [e.g., k8s cluster, local docker-compose, CLI tool or NEEDS CLARIFICATION]  
**Project Type**: [backend-only / frontend+backend / batch / internal tool or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, latency targets or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, auth rules, compliance, resource limits or NEEDS CLARIFICATION]  
**Scale/Scope**: [expected usage, affected services/modules, blast radius or NEEDS CLARIFICATION]

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Summarize the applicable gates derived from `/docs/constitution.md`.  
For each relevant constraint, indicate whether this plan currently **conforms**,  
and if not, why an exception might be needed.]

Example structure:

- **Safety / Security**: [OK / NEEDS REVIEW – reason]  
- **Maintainability**: [OK / NEEDS REVIEW – reason]  
- **Complexity / Scope Creep**: [OK / NEEDS REVIEW – reason]  
- **Testing / Observability**: [OK / NEEDS REVIEW – reason]

If any gate is **not** satisfied and no justification is provided, the plan should be considered BLOCKED until clarified.

---

## Project Structure

### Documentation (this feature)

```text
plans/<scope>/<service-or-system>/<EPIC-ID>/features/[FEATURE_ID]/
├── spec.md               # Feature specification (/speckit.specify output)
├── impl-plan.md          # This file (/speckit.plan output)
├── research.md           # Phase 0 output (/speckit.plan)
├── data-model.md         # Phase 1 output (/speckit.plan)
├── quickstart.md         # Phase 1 output (/speckit.plan)
├── contracts/            # Phase 1 output (/speckit.plan) - API / schema contracts
├── checklists/
│   └── requirements.md   # Spec quality checklist (/speckit.specify, then validated)
└── tasks.md              # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Epic-level Design (cross-feature context)

```text
plans/<scope>/<service-or-system>/<EPIC-ID>/
├── exec-plan.md          # Epic-level execution plan (required)
└── design/
    └── index.md          # Lightweight design index (optional but recommended)
                           # - Lists all features in the epic
                           # - Maps shared entities/APIs to owning feature(s)
                           # - Describes cross-feature dependencies and flows
```

This feature’s design (data-model, contracts, quickstart) should be reflected in
`design/index.md` when it introduces shared entities, endpoints, or invariants
that affect other features in the same epic.

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder structure below with the concrete
  layout actually used in this repository for this feature.

  - Delete unused options.
  - Replace <service-name> and other placeholders with real paths under services/.
  - The final plan must not include "Option N" labels; it should describe the
    actual agreed structure for this feature.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single service touched (common case)
services/
  <service-name>/
    src/
    tests/

tests/
  e2e/
    ... scenarios exercising this feature ...

# [REMOVE IF UNUSED] Option 2: API gateway + downstream service(s)
services/
  api-gateway/
    src/
    tests/
  <downstream-service>/
    src/
    tests/

tests/
  e2e/
    ... end-to-end flows across api-gateway + downstream-service ...

# [REMOVE IF UNUSED] Option 3: Multiple services and shared library
services/
  <service-a>/
  <service-b>/
  shared-lib/           # Shared code (if applicable)

tests/
  e2e/
  contract/
  integration/
```

**Structure Decision**:
[Document the selected structure and reference the real directories captured above.
If new directories or modules are introduced, justify them briefly and note any
impact on other features in the same epic.]

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**
> (e.g., Adding a new service, introducing a large library, designing that crosses existing boundaries, etc.)

| Violation / Risk                           | Why Needed (Current Need)            | Simpler Alternative Rejected Because             |
| ------------------------------------------ | ------------------------------------ | ------------------------------------------------ |
| [e.g., New shared library under services/] | [specific justification]             | [why extending existing module was insufficient] |
| [e.g., Cross-epic coupling]                | [specific cross-cutting requirement] | [why decoupled approach was not feasible]        |
| [e.g., Additional external dependency]     | [capability it provides]             | [why built-in / existing stack was insufficient] |

If this table is non-empty, make sure related decisions are also captured in:

* The epic’s `exec-plan.md` → **Decision Log**
* (If relevant) `plans/<...>/<EPIC-ID>/design/index.md` → shared design context