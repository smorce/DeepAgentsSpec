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

- ID: DEC-2026-006
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Introduce an in-repo System of Record for agent harness evolution with a six-blog-only source radar and mechanical control loop.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-007
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Consolidate control-loop execution into a single entrypoint (`harness/agent_radar/radar_ops.py`) with mode switching.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-008
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Add `backlog` step and daily GitHub Actions cycle to continuously convert source diffs into experiment backlog items.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-009
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Retire `EPIC-SYS-001-FOUNDATION` and remove its artifacts/references to keep the active SoR surface minimal.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-010
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Standardize unattended growth on `autogrow` mode, including backlog-to-implementation promotion, monitoring targets, and automatic rule encoding.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-011
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Restore `harness/feature_list.json` as full SoR that includes both system and service epics/features.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-012
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Fail validation when monitoring targets exist and bootstrap mode remains older than 24 hours.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-013
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Automatically transition monitoring loop label from bootstrap to autogrow after first successful control loop.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-014
  Date: 2026-02-13
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Introduce isolated worktree harness runner for one-shot reproduce/fix/verify/evidence workflow.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-015
  Date: 2026-02-14
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Expand article-to-task conversion beyond MCP/Skills and enforce doc-gardening freshness checks against SoR backlog state.
  Details: See ExecPlan at:
    - plans/system/EPIC-SYS-001-harness-radar/exec-plan.md (Decision Log)

- ID: DEC-2026-016
  Date: 2026-02-22
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: Harness V2 パイプライン導入。V1のタイトル/URL収集+タグ付けmutationから、記事本文分析→ギャップ分析→多段レビューループ→実コード改修へ全面刷新。
  Details: V1のmutation（83個）は全てテンプレ生成の純関数で実質的な改善を行っていなかった。V2では (1) Codex CLIで記事本文を読みアイデア抽出、(2) コードベースとのギャップ分析（現状→理想→差分をSoR化）、(3) Codex CLI非対話モードの多段レビュー（最大5セッション、5軸評価）、(4) レビュー通過後に実際のコードベース改修を実行する。不採用アイデアも理由付きで永続化する。設計書: docs/agent-harness/harness-v2-design.md

- ID: DEC-2026-017
  Date: 2026-02-22
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: レビューループにCodex CLI非対話モードのマルチセッション方式を採用。各セッションはコンテキストリセットされた状態で独立評価し、レビューコメントは共通ファイルに蓄積。
  Details: scripts/run_v2_review_loop.sh でforループ実行。評価5軸（ハーネス関連性/実現可能性/リスク/ROI/SoR整合性）、全スコア3以上かつ平均3.5以上で承認。最大5セッション超過時はneeds_human_review。

- ID: DEC-2026-018
  Date: 2026-02-22
  Scope: system
  Related epics: EPIC-SYS-001-HARNESS-RADAR
  Summary: ディレクトリ構造変更をSoR化する方式を採用。マークダウンのリスト形式で構造を定義→変更スクリプト生成→実行の三段階とし、ロールバックスクリプトも併せて生成する。
  Details: harness/agent_radar/executions/EXEC-*/dir-structure.md にディレクトリ構造を記録、change-script.py で実行、rollback-script.py でロールバック可能とする。
