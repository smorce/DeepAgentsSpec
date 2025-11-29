# ExecPlans

This directory contains ExecPlans for all epics in this repository.

ExecPlans are executable specifications that must be written and maintained according to `./PLANS.md` at the repository root.

- System-wide epics go under `plans/system/`.
- Service-specific epics go under `plans/services/<service-name>/`.

Each ExecPlan must:
- Be fully self-contained and novice-friendly.
- Include an `Epic Metadata` section that links to `harness/feature_list.json`.
- List all in-scope features (by id and title) for this epic.
- Be kept up to date as a living document while implementation progresses.