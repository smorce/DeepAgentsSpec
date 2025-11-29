# EPIC-SYS-001-FOUNDATION: System foundation and scaffolding

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository stores the ExecPlan guidelines in `./PLANS.md` at the repository root. This document must be maintained in accordance with PLANS.md.

## Epic Metadata

Epic ID: EPIC-SYS-001-FOUNDATION  
ExecPlan path (from repo root): plans/system/EPIC-SYS-001-foundation.md  
Feature list file: harness/feature_list.json  
In-scope features (from `harness/feature_list.json` where `features[].epic_id == "EPIC-SYS-001-FOUNDATION"`):

- F-SYS-001: Repository scaffold initialized

Related services:

- api-gateway
- user-service
- billing-service

## Purpose / Big Picture

Ensure the repository layout, harness, and baseline tooling are defined so future agents can work reliably. The goal is to have a repeatable scaffold that describes the architecture, contains centralized feature tracking, and provides scripts that guard the quality gates (unit, integration, and e2e).

## Progress

- [ ] (YYYY-MM-DD hh:mmZ) Repository layout with architecture, plans, services, tests, and docs created.
- [ ] (YYYY-MM-DD hh:mmZ) Harness files (`init.sh`, `feature_list.json`, etc.) added and validated.
- [ ] (YYYY-MM-DD hh:mmZ) Baseline scripts in `scripts/` and service directories show placeholder behavior.
- [ ] (YYYY-MM-DD hh:mmZ) Verification steps recorded in Validation and Acceptance along with exact commands and outputs.

## Surprises & Discoveries

- Observation:

  Describe any unexpected repository layout challenges, tool constraints, or Rock issues encountered while bootstrapping the scaffold.

  Evidence:

    Include short, indented snippets of console output or configuration files that illustrate the observation.

## Decision Log

- Decision:

  Repository layout follows the “architecture → microservices” template provided in the initialization prompt to keep ExecPlans central and services isolated.

  Rationale:

  A consistent structure makes it easier for future agents to locate artifacts without traversing custom paths.

  Date/Author:

  YYYY-MM-DD / coding-agent

## Outcomes & Retrospective

Summarize what was achieved for this epic, highlight which tools are now available for future work, and note any leftover housekeeping (e.g., missing PLANS.md content that the user will provide later).

Mention:

- Which features (F-SYS-001) are now "passing".
- Any follow-up epics or features that should be created.
- Any lingering scaffolding tasks or TODOs.

## Context and Orientation

This epic touches:

- Repository root: organizes PLANS.md, harness, architecture, services, tests, scripts, and docs.
- `harness/feature_list.json`: powers ExecPlan referencing and feature tracking.
- `scripts/`, `services/*/scripts/`: provide entry points for running the suite.

Non-obvious terms:

- "Harness": the shared folder containing orchestration scripts, feature tracking, and progress logs.
- "ExecPlan": an executable plan that documents the steps to implement a specific epic.

## Plan of Work

1. Create the architecture and documents that describe the system.
2. Populate the harness with init scripts, feature tracking, and configuration.
3. Scaffold the services directories with placeholders in `src`, `tests`, `scripts`, and config files.
4. Create the shared `scripts/` helpers and docs that the team will rely on.
5. Verify the structure with `ls`/`tree` and update the Validation and Acceptance section.

## Concrete Steps

These steps assume you are at the repository root.

1. Orientation and feature selection:

    Run:

        pwd

        ls

        cat harness/feature_list.json

        cat plans/README.md

    Confirm this executes without errors and matches the expected template (features failing).

2. Populate architecture docs:

    - Create `architecture/system-architecture.md`, `architecture/service-boundaries.md`, and `architecture/deployment-topology.md`.
    - Add guidance about diagrams under `architecture/diagrams/README.md`.

3. Scaffold harness:

    - Add `harness/init.sh`, `harness/feature_list.json`, `harness/harness-config.yaml`, `harness/AI-Agent-progress.txt`.
    - Ensure `init.sh` is executable and logs each step.

4. Service scaffolding:

    - For each service (`api-gateway`, `user-service`, `billing-service`), create `README.md`, `service-architecture.md`, `src/`, `tests/unit`, `tests/integration`, `scripts/`, `Dockerfile`, `service-config.example.yaml`.
    - Populate scripts with safe placeholder commands.

5. Shared helpers and docs:

    - Create `scripts/run_all_unit_tests.sh`, `scripts/run_all_e2e_tests.sh`, `scripts/format_or_lint.sh`.
    - Add `docs/onboarding.md`, `docs/decisions.md`, `docs/operations.md`.

6. Validation:

    - Run `ls -R` or similar to inspect structure; record commands and output here.
    - Confirm directories line up with ExecPlans.

## Validation and Acceptance

Document the exact commands executed and the observed behavior.

- Command:

      ls

  Observed:

      Directory listing contains architecture/, harness/, plans/, services/, tests/, scripts/, docs/.

- Command:

      ls services/api-gateway

  Observed:

      README.md, service-architecture.md, src/, tests/, scripts/, Dockerfile, service-config.example.yaml.

Add more commands once tests or scripts are run.

## Idempotence and Recovery

- Running the scaffold creation steps again should overwrite placeholder files without damaging real logic.
- Scripts are echoes so rerunning them will not change state.
- Document any additional rollback steps here if future modifications expand beyond scaffolding.

## Artifacts and Notes

- Example scaffold verification:

    $ ls services

      api-gateway  user-service  billing-service

- Example test placeholder:

    $ scripts/run_all_unit_tests.sh

      [run_all_unit_tests.sh] Placeholder – add real commands in later cycles.

## Interfaces and Dependencies

- No runtime interfaces yet; each service has a `service-config.example.yaml` that must be filled in later.
- Scripts rely on bash, but they only echo guidance, so they have no external dependencies.

