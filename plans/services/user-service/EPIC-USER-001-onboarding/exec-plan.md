# EPIC-USER-001-ONBOARDING: User onboarding flow

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository stores the ExecPlan guidelines in `./PLANS.md` at the repository root. This document must be maintained in accordance with PLANS.md.

## Epic Metadata

Epic ID: EPIC-USER-001-ONBOARDING  
ExecPlan path (from repo root): plans/services/user-service/EPIC-USER-001-onboarding.md  
Feature list file: harness/feature_list.json  

In-scope features (from `harness/feature_list.json` where `features[].epic_id == "EPIC-USER-001-ONBOARDING"`):

- F-USER-001: Signup page basic UI
- F-USER-002: Signup API endpoint

Related services:

- api-gateway
- user-service

## Purpose / Big Picture

After implementing this epic, a new user will be able to sign up for an account through a simple onboarding flow. A user can open the signup page in a browser, fill in the required fields, submit the form, and see a clear indication that the signup was successful.

From a user perspective, the main observable behavior is:

- Navigating to a browser URL such as `http://localhost:8080/signup` shows a signup form.
- Submitting valid signup information results in account creation and a success confirmation (for example, a redirect to a welcome page or a success message).
- Submitting invalid or incomplete data shows helpful error messages without crashing the system.

## Progress

- [ ] (YYYY-MM-DD hh:mmZ) Initial orientation and repository scan completed.
- [ ] (YYYY-MM-DD hh:mmZ) Signup page route and basic UI skeleton implemented (F-USER-001).
- [ ] (YYYY-MM-DD hh:mmZ) Signup API endpoint implemented and wired to persistence (F-USER-002).
- [ ] (YYYY-MM-DD hh:mmZ) Unit and integration tests added and passing for both features.
- [ ] (YYYY-MM-DD hh:mmZ) End-to-end test scenario for the onboarding flow implemented and passing.
- [ ] (YYYY-MM-DD hh:mmZ) Feature statuses updated to "passing" in `harness/feature_list.json` and final retrospective written.

## Surprises & Discoveries

- Observation:
  Describe any unexpected behavior, dependency issues, framework quirks, or performance characteristics discovered while implementing this epic.

  Evidence:
    Include short, indented snippets of test output or logs that illustrate the observation.

## Decision Log

- Decision:
  Describe each design or scope decision related to this epic, such as choosing a specific routing pattern, validation approach, or data model.

  Rationale:
  Explain why this decision was made in plain language, including trade-offs where relevant.

  Date/Author:
  YYYY-MM-DD / coding-agent or human name.

- Decision:
  Additional decisions are appended here over time, keeping this section as the single source of truth for this epic.

## Outcomes & Retrospective

Summarize what was achieved for this epic, what remains, and any lessons learned. Compare the final behavior against the original Purpose / Big Picture.

Mention:

- Which features (F-USER-001, F-USER-002) are now "passing".
- Any follow-up epics or features that should be created.
- Any lingering technical debt or shortcuts taken.

## Context and Orientation

This epic touches the following key parts of the repository:

- `services/api-gateway/src/...`  
  Routes HTTP requests such as `GET /signup` and `POST /api/users` to the appropriate handlers.

- `services/user-service/src/...`  
  Implements the business logic and persistence for user creation.

- `tests/e2e/scenarios/user_onboarding.spec.ts`  
  Contains the end-to-end scenario that drives a real browser (for example, using Puppeteer) to exercise the whole onboarding flow.

Non-obvious terms:

- "API gateway": The microservice that receives incoming HTTP requests from clients and routes them to backend services. In this repository it lives under `services/api-gateway/`.
- "End-to-end (E2E) test": A test that exercises the system from the outside, in the same way a user would, typically using a real or headless browser.

## Plan of Work

The work proceeds in small, verifiable steps that gradually build the onboarding flow.

First, prepare the routing and UI skeleton for the signup page in `services/api-gateway`. Add a route handler for `GET /signup` that renders a minimal HTML page or template with a signup form. At this stage, the form does not need to be fully functional; it is enough that the page loads successfully in a browser.

Next, implement the signup API endpoint in both `services/api-gateway` and `services/user-service`. In the API gateway, add a `POST /api/users` route that validates the incoming request payload and forwards the data to the user service. In the user service, create a handler that performs basic validation and persistence, then returns an appropriate success or error response.

After the basic flow is in place, add unit tests and integration tests for both services. For example, test that the signup handler returns the correct HTTP status codes and errors for valid and invalid payloads. Ensure that the user record is stored correctly in the chosen persistence layer.

Finally, create an end-to-end test scenario under `tests/e2e/scenarios/user_onboarding.spec.ts`. This scenario should start the system, open the signup page in a browser, submit a valid signup form, and verify that the user sees a success indication. The same scenario can also test invalid inputs to confirm that validation errors are displayed.

At each step, keep this Plan of Work aligned with reality. If discoveries require changes in approach, update this section and record the reasoning in the Decision Log.

## Concrete Steps

These steps assume you are at the repository root.

1. Orientation and feature selection:

    Run:

        pwd
        cat PLANS.md | head -n 20
        cat harness/feature_list.json

    Confirm that this ExecPlan corresponds to epic `EPIC-USER-001-ONBOARDING` and that features `F-USER-001` and `F-USER-002` are in scope.

2. Implement signup page UI (F-USER-001):

    - Edit the routing file in `services/api-gateway/src/` to add a handler for `GET /signup`.
    - Implement a minimal HTML or template that shows a form with fields such as email and password.

    Example commands:

        cd services/api-gateway
        # open the relevant source file and implement the handler
        cd ../../

3. Implement signup API endpoint (F-USER-002):

    - In `services/api-gateway`, add a `POST /api/users` route that accepts JSON or form data.
    - In `services/user-service`, add a handler that receives signup data, validates it, and persists a new user.

4. Add unit and integration tests:

    - In `services/api-gateway/tests/unit/`, add tests that exercise the new routes.
    - In `services/user-service/tests/integration/`, add tests that verify user creation and error handling.

5. Implement E2E scenario:

    - In `tests/e2e/scenarios/user_onboarding.spec.ts`, write a test that:
      - Starts the system using `harness/init.sh` or the appropriate script.
      - Opens `http://localhost:8080/signup`.
      - Fills in the form, submits it, and verifies success.

6. Run tests:

    Example commands:

        ./harness/init.sh
        scripts/run_all_unit_tests.sh
        scripts/run_all_e2e_tests.sh

    Record the exact commands and outcomes in this section as work progresses.

7. Update shared artifacts:

    - When a feature is complete and validated, update its `status` in `harness/feature_list.json` to `passing`.
    - Reflect this in the Progress section above with timestamps.
    - Append a summary of the session to `harness/AI-Agent-progress.txt`.

## Validation and Acceptance

The onboarding flow for this epic is considered accepted when all of the following conditions are met:

- Starting the system (for example with `./harness/init.sh` or another documented command) succeeds without errors.
- In a browser, navigating to `http://localhost:8080/signup` shows a signup form.
- Submitting a valid signup form results in:
  - HTTP 201 or an equivalent success response from `POST /api/users`.
  - A visible success message or redirect to a welcome page.
- Submitting invalid data shows clear validation errors while keeping the page responsive.
- All relevant unit, integration, and E2E tests pass, including the onboarding scenario test.

Document the exact commands used and the observed outputs so that a novice can replicate the validation.

## Idempotence and Recovery

All steps in this plan are designed to be safe to repeat:

- Running `./harness/init.sh` multiple times should not corrupt the environment; it should reinstall dependencies and re-run tests as needed.
- Adding or modifying source files and tests should be done in a way that keeps Git history clean; commit frequently with clear messages referencing this epic and feature IDs.
- If a migration or destructive change is needed (such as altering a database schema), document backup and rollback steps here before performing the change.

If a step fails halfway, update the Progress section to reflect the partial completion, describe the failure briefly, and explain how to retry safely.

## Artifacts and Notes

Use this section to capture short, focused snippets that prove success:

- Example unit test output summary.
- Example E2E test run summary.
- Short diffs or code excerpts that illustrate key changes.

For instance:

    Example: e2e test run
    $ scripts/run_all_e2e_tests.sh
      ✔ user_onboarding.spec.ts (1 test, 1 passed)

Keep these snippets concise and directly tied to the behaviors described in this plan.

## Interfaces and Dependencies

Be explicit about the interfaces this epic introduces or depends on.

For example, in `services/api-gateway/src/routes/signup.ts` define a handler conceptually similar to:

    handle_get_signup(request) -> response

that renders the signup page.

For the signup API, define an endpoint conceptually similar to:

    POST /api/users
    Request body:
      {
        "email": "user@example.com",
        "password": "string with minimum length"
      }

    Responses:
      201 Created on success
      400 Bad Request with a JSON body describing validation errors

In `services/user-service/src/handlers/signup.ts`, define a function that takes validated signup data, persists a new user, and returns a result that can be mapped to HTTP responses in the API gateway.

Document any external libraries or frameworks used (for example, web frameworks, ORMs, or validation libraries) so that a novice can understand the dependencies and locate their configuration in the repository.

---

Revision note:

- YYYY-MM-DD: Initial version of this ExecPlan created from the template and aligned with `harness/feature_list.json`.