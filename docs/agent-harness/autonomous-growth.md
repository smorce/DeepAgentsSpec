# Autonomous Growth

この文書は、自律成長ループの実装結果を記録する SoR です。

- Updated at: `2026-02-13T07:36:17Z`

## Backlog Status

| EXP ID | Status | Themes | Artifacts |
| --- | --- | --- | --- |
| EXP-001 | implemented | mcp, skills | harness/agent_radar/implemented/EXP-001/spec.md, harness/agent_radar/implemented/EXP-001/impl-plan.md, harness/agent_radar/implemented/EXP-001/state-strategy.json, harness/agent_radar/mutations/mutation_exp_001.py |

## Runbook

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2`
