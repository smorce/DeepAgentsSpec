# Architecture and Design Decisions Index

This file is an index of important architecture and design decisions across the repository.

The primary, detailed record for each decision lives in the `Decision Log` section of the corresponding ExecPlan under `plans/`. This file provides a cross-referenced summary so that readers can quickly discover what was decided and where to find the full context.

## Format

Each entry should follow this format:

- ID: DEC-YYYY-NNN
  Date: YYYY-MM-DD
  Scope: system | service:<service-name> | multi-service
  Related epics: EPIC-XXXX-..., EPIC-YYYY-...
  Summary: One-line description of the decision.
  Details: See ExecPlan(s) at:
    - plans/.../EPIC-....md (Decision Log)

## Entries

- ID: DEC-2025-001
  Date: 2025-01-01
  Scope: system
  Related epics: EPIC-SYS-001-FOUNDATION
  Summary: Adopt "architecture → microservices" repository layout with a global feature_list.json and epic-level ExecPlans.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-foundation.md (Decision Log)

- ID: DEC-2025-002
  Date: 2025-01-01
  Scope: multi-service
  Related epics: EPIC-USER-001-ONBOARDING
  Summary: Implement user onboarding flow via api-gateway and user-service with an HTTP-based integration.
  Details: See ExecPlan at:
    - plans/services/user-service/EPIC-USER-001-onboarding.md (Decision Log)

- ID: DEC-2026-001
  Date: 2026-01-02
  Scope: service:api-gateway
  Related epics: EPIC-API-002-MINIRAG
  Summary: Require MINIRAG_DB_DSN for persistent storage and allow in-memory only when explicitly enabled.
  Details: See ExecPlan at:
    - plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md (Decision Log)

- ID: DEC-2026-002
  Date: 2026-01-03
  Scope: service:avatar-ui
  Related epics: EPIC-AVATAR-001-DIARY-MINIRAG
  Summary: Finalize diary conversations via explicit UI action and register structured entries to MiniRAG with fixed workspace "diary".
  Details: See ExecPlan at:
    - plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md (Decision Log)

- ID: DEC-2026-003
  Date: 2026-01-03
  Scope: service:avatar-ui
  Related epics: EPIC-AVATAR-001-DIARY-MINIRAG
  Summary: Persist search toggle/top_k per thread on the server and distribute defaults via /agui/config for tool + UI alignment.
  Details: See ExecPlan at:
    - plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md (Decision Log)

- ID: DEC-2026-004
  Date: 2026-01-03
  Scope: service:avatar-ui
  Related epics: EPIC-AVATAR-001-DIARY-MINIRAG
  Summary: Update user profiling via diff-based updates that never overwrite non-empty values with empty data and surface failures in UI without blocking diary registration.
  Details: See ExecPlan at:
    - plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md (Decision Log)

- ID: DEC-2026-005
  Date: 2026-01-03
  Scope: service:avatar-ui
  Related epics: EPIC-AVATAR-001-DIARY-MINIRAG
  Summary: Validate profiling updates against the default profile schema and apply only above a confidence threshold.
  Details: See ExecPlan at:
    - plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md (Decision Log)
