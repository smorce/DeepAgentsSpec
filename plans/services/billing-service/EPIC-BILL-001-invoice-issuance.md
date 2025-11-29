# EPIC-BILL-001-INVOICE-ISSUANCE: Billing service invoice issuance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository stores the ExecPlan guidelines in `./PLANS.md` at the repository root. This document must be maintained in accordance with PLANS.md.

## Epic Metadata

Epic ID: EPIC-BILL-001-INVOICE-ISSUANCE  
ExecPlan path (from repo root): plans/services/billing-service/EPIC-BILL-001-invoice-issuance.md  
Feature list file: harness/feature_list.json  
In-scope features (from `harness/feature_list.json` where `features[].epic_id == "EPIC-BILL-001-INVOICE-ISSUANCE"`):

- TBD

Related services:

- billing-service

## Purpose / Big Picture

Define how the billing service will generate invoices, issue them through a REST endpoint, and expose enough metadata for observability. The goal is to have a documented contract before any implementation work begins.

## Progress

- [ ] (YYYY-MM-DD hh:mmZ) Establish requirements for invoice generation and external integrations.
- [ ] (YYYY-MM-DD hh:mmZ) Sketch HTTP endpoints in `services/billing-service/src`.
- [ ] (YYYY-MM-DD hh:mmZ) Document configuration and scripts.

## Surprises & Discoveries

- Observation:

  Capture any findings about billing domain complexity, tax rules, or dependencies.

  Evidence:

    Include short, indented snippets of research notes or logs.

## Decision Log

- Decision:

  Create `service-architecture.md` and config templates before implementing the logic so that future developers have a frame of reference.

  Rationale:

  Early documentation reduces assumptions later in the epic.

  Date/Author:

  YYYY-MM-DD / coding-agent

## Outcomes & Retrospective

Summarize what was achieved with the billing scaffolding, next steps for invoicing logic, and lessons learned.

Mention:

- Which features (if any) are now "passing".
- Any follow-up epics or features that should be created.
- Any technical debt discovered while drafting this plan.

## Context and Orientation

This epic touches:

- `services/billing-service/src/`
- `services/billing-service/tests/`
- `services/billing-service/scripts/`

Non-obvious terms:

- "Invoice issuance": the process of generating, storing, and delivering a charge summary to a customer.

## Plan of Work

1. Document the billing service responsibilities and necessary external interfaces.
2. Sketch placeholder HTTP surface and persistence connectors.
3. Provide documentation and script stubs for the billing service workflow.
4. Keep this ExecPlan aligned with any future additions to `harness/feature_list.json`.

## Concrete Steps

These steps assume you are at the repository root.

1. Orientation and feature selection:

    Run:

        pwd

        ls plans/services/billing-service

        cat harness/feature_list.json

    Confirm whether new billing features need to be added to the feature list.

2. Service scaffolding:

    - Create `services/billing-service/src/` sprite.
    - Set up `Dockerfile`, `service-config.example.yaml`, and scripts with TODO placeholders.
    - Add `.gitkeep` files inside tests to preserve structure.

3. Validation:

    - Record commands such as `scripts/run_all_unit_tests.sh` once they exist.

## Validation and Acceptance

Once real logic exists, record:

- Command:

      scripts/run_all_unit_tests.sh

  Observed:

      Placeholder output (to update later).

- Command:

      ls services/billing-service

  Observed:

      README, service-architecture, Dockerfile, service-config, src/, tests/, scripts/.

## Idempotence and Recovery

- Scripts and docs can be overwritten safely since they are placeholders.
- Add rollback notes here when real persistence or data migrations are introduced.

## Artifacts and Notes

- Example placeholder invocation:

    $ scripts/run_all_unit_tests.sh

      [run_all_unit_tests.sh] Placeholder – implement actual test commands.

## Interfaces and Dependencies

- No runtime interfaces implemented yet; future work will add invoice endpoints and connectors.

