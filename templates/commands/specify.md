---
description: From a natural-language product description, auto-generate epics/features, update harness/feature_list.json, create spec.md & requirements checklist for each feature, then hand off to clarify/plan.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
---

## User Input

```text
$ARGUMENTS
````

You **MUST** treat `$ARGUMENTS` as the whole product description. No feature ID is required.

## Outline

The text after `/speckit.specify` **is** the whole product description. From it, you must derive epics/features, write specs, and update the repository. No pre-existing `feature_list.json` entries are assumed.

Execution flow:

1. **Parse product description**  
   - Extract candidate epics and features (aim for 1–5 features unless the description clearly implies more).  
   - Assign responsible services from the known set: `api-gateway`, `user-service`, `billing-service` (add more only if already present in the repo).  
   - Summarize each feature with title + 1–2 sentence description.

2. **Assign IDs (auto)**  
   - Read or create `harness/feature_list.json`.  
   - Epic ID format: `EPIC-<CODE>-NNN-<slug>` where `<CODE>` is service code (API/USER/BILL/GEN). Pick NNN as max existing for that code + 1.  
   - Feature ID format: `F-<CODE>-NNN` with the same numbering rule.  
   - Avoid collisions; if collision occurs, increment NNN.  
   - Set `exec_plan_path` to `plans/services/<service>/<epic_id_lower>/exec-plan.md`.

3. **Update `harness/feature_list.json`**  
   - Append new epics/features with fields: `id`, `epic_id`, `title`, `description`, `services`, `status`="failing", `tags` (optional), `spec_path`, `checklist_path`.  
   - `spec_path` = `plans/services/<service>/<epic_id_lower>/features/<feature_id>/spec.md`  
   - `checklist_path` = same dir + `/checklists/requirements.md`  
   - Create parent directories as needed.

4. **Scaffold files per feature**  
   - Create directories for `spec.md` and `checklists/requirements.md`.  
   - Copy `templates/spec-template.md` into `spec.md`, then fill placeholders using the feature summary (title/ID/date/branch-name may be generic).  
   - Write `checklists/requirements.md` using the checklist template below (all unchecked).

5. **Write the specification content** for each feature  
   - Follow the guidance in “Specification writing” (see below) using the original product description and the feature summary.  
   - Keep tech-agnostic; limit to WHAT/WHY.  
   - Add at most 3 `[NEEDS CLARIFICATION: ...]` markers for high-impact unknowns.

6. **Output**  
   - List created epics and features with their IDs and `spec.md` paths.  
   - Remind the user that `/speckit.clarify` と `/speckit.plan` を次に実行する。  
   - If any step failed, fix it automatically (retry; create missing dirs; regenerate IDs) and proceed; report only remaining blockers.

### Specification writing (per feature)

* Extract key concepts: actors, actions, data, constraints, success signals, failure modes.  
* User Scenarios & Testing: primary happy path + 1–2 edge/error paths.  
* Functional Requirements: testable, numbered, no implementation detail.  
* Success Criteria: measurable, tech-agnostic (latency/accuracy/UX completion).  
* Assumptions: defaults you made.  
* `[NEEDS CLARIFICATION: question]` up to 3.

### Checklist template (write to `.../checklists/requirements.md`)

```markdown
# Specification Quality Checklist: [FEATURE NAME]

**Purpose**: Validate specification completeness and quality before proceeding to planning  
**Created**: [DATE]  
**Feature**: [Link to spec.md]

## Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

## Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic
- [ ] All acceptance scenarios are defined
- [ ] Edge cases are identified
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

## Feature Readiness
- [ ] All functional requirements have clear acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria
- [ ] No implementation details leak into specification

## Notes
- Items marked incomplete require spec updates before `/speckit.plan`
```

### Reporting
Provide:
- Created epic IDs and exec_plan paths (files may be empty placeholders).
- Created feature IDs with spec/checklist paths.
- Any `[NEEDS CLARIFICATION]` items per feature.
- Reminder to run `/speckit.clarify` then `/speckit.plan`.

### General Guidelines
* Focus on **WHAT** and **WHY**, not HOW.  
* Remove sections that don’t apply; don’t leave “N/A”.  
* Keep `[NEEDS CLARIFICATION]` ≤ 3 per feature.  
* Specs should be understandable to non-technical stakeholders.

3. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use only for critical decisions that:

   * Significantly impact feature scope or user experience
   * Have multiple reasonable interpretations with different implications
   * Lack any reasonable default

4. **Prioritize clarifications**: scope > security/privacy > user experience > technical details

5. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item

6. **Common areas needing clarification** (only if no reasonable default exists):

   * Feature scope and boundaries (include/exclude specific use cases)
   * User types and permissions (if multiple conflicting interpretations possible)
   * Security/compliance requirements (when legally/financially significant)

**Examples of reasonable defaults** (don't ask about these):

* Data retention: Industry-standard practices for the domain
* Performance targets: Standard web/mobile app expectations unless specified
* Error handling: User-friendly messages with appropriate fallbacks
* Authentication method: Standard session-based or OAuth2 for web apps
* Integration patterns: RESTful APIs unless specified otherwise

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

* "Users can complete checkout in under 3 minutes"
* "System supports 10,000 concurrent users"
* "95% of searches return results in under 1 second"
* "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

* "API response time is under 200ms" (too technical, use "Users see results instantly")
* "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
* "React components render efficiently" (framework-specific)
* "Redis cache hit rate above 80%" (technology-specific)
