# EPIC-API-001-ROUTING: API gateway basic routing

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository stores the ExecPlan guidelines in `./PLANS.md` at the repository root. This document must be maintained in accordance with PLANS.md.

## Epic Metadata

Epic ID: EPIC-API-001-ROUTING  
ExecPlan path (from repo root): plans/services/api-gateway/EPIC-API-001-routing.md  
Feature list file: harness/feature_list.json  
In-scope features (from `harness/feature_list.json` where `features[].epic_id == "EPIC-API-001-ROUTING"`):

- F-API-001: Basic health check endpoint

Related services:

- api-gateway

## Purpose / Big Picture

Deliver the API gateway routing surface with at least one health-check endpoint so the system exposes a reliable entry point. This forms the minimal API required before downstream services are wired in.

## Progress

- [ ] (YYYY-MM-DD hh:mmZ) Define route handlers in `services/api-gateway/src`.
- [ ] (YYYY-MM-DD hh:mmZ) Add unit tests for the routing handlers.
- [ ] (YYYY-MM-DD hh:mmZ) Configure Dockerfile and service config samples.
- [ ] (YYYY-MM-DD hh:mmZ) Validate the GET `/health` endpoint returns HTTP 200.

## Surprises & Discoveries

- Observation:

  Document any unexpected constraints, such as missing frameworks, template engines, or validation libraries.

  Evidence:

    Include short snippets of logs or config differences.

## Decision Log

- Decision:

  Keep the API gateway service readable and ready for further work by including a dedicated `service-architecture.md`, placeholder scripts, and README guidance.

  Rationale:

  Providing local documentation reduces onboarding friction and serves as the first point of reference for routing decisions.

  Date/Author:

  YYYY-MM-DD / coding-agent

## Outcomes & Retrospective

Summarize what was achieved by implementing the API gateway skeleton, what remains (e.g., actual handler logic), and whether rerunning the placeholder scripts still behaves as expected.

Mention:

- Which features (F-API-001) are now "passing".
- Any follow-up epics or features that should be created for further routing enhancements.
- Any unexpected testing gaps uncovered during the bootstrap.

## Context and Orientation

This epic touches:

- `services/api-gateway/src/`: new route handlers and middleware.
- `services/api-gateway/tests/`: unit and integration test stubs for the API surface.
- `services/api-gateway/scripts/`: helper scripts referenced by the harness.

Non-obvious terms:

- "API gateway": the microservice that accepts HTTP requests and forwards them to backend services.
- "Health check": a lightweight endpoint used by infrastructure to verify the service is alive.

## Plan of Work

1. Sketch routing requirements for the API gateway (GET `/health` etc.).
2. Implement placeholder handlers in `services/api-gateway/src`.
3. Add test stubs under `services/api-gateway/tests/unit`.
4. Fill service-level documentation and configuration samples.
5. Document validation steps and commands under Validation and Acceptance.

## Concrete Steps

These steps assume you are at the repository root.

1. Orientation and feature selection:

    Run:

        pwd

        cat plans/services/api-gateway/EPIC-API-001-routing.md

        cat harness/feature_list.json

    Confirm the epic aligns with F-API-001.

2. Routing scaffold:

    - Create `services/api-gateway/src/README.md` or handler files.
    - Add GET `/health` route placeholder and supporting README content.

3. Testing scaffold:

    - Add `.gitkeep` or skeleton test files under `services/api-gateway/tests/unit`.
    - Document how to run them from `scripts/run_all_unit_tests.sh`.

4. Build scaffolding:

    - Provide `Dockerfile` with TODO comments.
    - Add `service-config.example.yaml` describing environment variables.

5. Validation:

    - Run `scripts/run_all_unit_tests.sh` and record output.
    - Use `curl http://localhost:8080/health` as a future check (description only).

## Validation and Acceptance

Record commands and results once real tests exist.

- Command:

      scripts/run_all_unit_tests.sh

  Observed:

      Placeholder script echoes its status.

- Command:

      ls services/api-gateway

  Observed:

      Contains README, service-architecture, src/, tests/, scripts/, Dockerfile, service-config.

## Idempotence and Recovery

- Running the placeholder scripts more than once is safe because they only echo informative messages.
- Configuration files contain comments describing where to put real values, so editing them is safe and reversible.

## Artifacts and Notes

- Example test stub output:

    $ scripts/run_all_unit_tests.sh

      [run_all_unit_tests.sh] Placeholder – implement actual test commands.

## Interfaces and Dependencies

- `services/api-gateway/src/` will expose HTTP routes such as GET `/health`.
- Tests rely on bash scripts and made-up entry points for now, so dependencies are minimal.

