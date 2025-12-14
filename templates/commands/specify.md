---
description: Create or update the feature specification from a natural language feature description.
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
````

You **MUST** consider the user input before proceeding (if not empty).

## Outline

The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Identify the target feature entry from `harness/feature_list.json`:**

   * Each feature is defined with an `id`, `title`, `spec_path`, and `services` list.
   * `/speckit.specify` must either receive the `--feature-id F-XXX-YYY` via `SPECIFY_FEATURE`
     (preferred), or infer it from context (e.g., `/speckit.specify F-USER-001 …`).
   * When unsure, filter the `feature_list.json` entries by service, search term, or explicit ID.
     The helper script already supports:

     * `--feature-id F-USER-001`
     * `--service api-gateway --search "health check"`

2. **Invoke `{SCRIPT}` (create-new-feature) with the resolved feature ID**:

   * Example bash command:

     ```bash
     scripts/bash/create-new-feature.sh --feature-id F-USER-001 "Implement signup flow"
     ```

   * Example PowerShell command:

     ```powershell
     scripts/powershell/create-new-feature.ps1 -FeatureId F-USER-001 "Implement signup flow"
     ```

   * The script automatically:

     * Looks up the feature metadata in `harness/feature_list.json`.
     * Creates/checkout the appropriate branch (using the repo’s naming convention).
     * Copies `templates/spec-template.md` into the `spec.md` path specified by the feature entry.
     * Creates `checklists/requirements.md` if missing.

   **IMPORTANT**:

   * Do **not** attempt to invent branch numbers manually; the harness chooses consistent naming based on the selected feature.
   * Always run `{SCRIPT}` exactly once per feature to avoid clobbering existing work.
   * The JSON output from `{SCRIPT}` will contain fields such as `BRANCH_NAME`, `SPEC_FILE`, `FEATURE_DIR`, and checklist paths. Use these values verbatim when writing the spec.
   * For single quotes in args like "I'm Groot", use escape syntax: e.g. `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`)

3. Load `templates/spec-template.md` to understand required sections.

4. Follow this execution flow:

   1. Parse user description from Input
      If empty: ERROR "No feature description provided"

   2. Extract key concepts from description
      Identify: actors, actions, data, constraints

   3. For unclear aspects:

      * Make informed guesses based on context and industry standards
      * Only mark with [NEEDS CLARIFICATION: specific question] if:

        * The choice significantly impacts feature scope or user experience
        * Multiple reasonable interpretations exist with different implications
        * No reasonable default exists
      * **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
      * Prioritize clarifications by impact: scope > security/privacy > user experience > technical details

   4. Fill User Scenarios & Testing section
      If no clear user flow: ERROR "Cannot determine user scenarios"

   5. Generate Functional Requirements
      Each requirement must be testable
      Use reasonable defaults for unspecified details (document assumptions in Assumptions section)

   6. Define Success Criteria
      Create measurable, technology-agnostic outcomes
      Include both quantitative metrics (time, performance, volume) and qualitative measures (user satisfaction, task completion)
      Each criterion must be verifiable without implementation details

   7. Identify Key Entities (if data involved)

   8. Return: SUCCESS (spec ready for clarification and planning)

5. **Write the specification to SPEC_FILE** using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.

   * SPEC_FILE is the full path returned in the JSON from `{SCRIPT}`.
   * Under the per-feature layout, SPEC_FILE will look like:

     * `plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/spec.md`
     * Example:

       * `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md`

6. **Specification Quality Checklist**: After writing the initial spec, generate a quality checklist file that will be used later by humans and tools (e.g. `/speckit.clarify`, `scripts/validate_spec.sh`) to validate the spec.

   * Let `FEATURE_DIR` be the directory that contains SPEC_FILE (i.e., the parent directory of `spec.md`).
     For example, if
     `SPEC_FILE = plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md`
     then
     `FEATURE_DIR = plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001`.

   a. **Create Spec Quality Checklist**: Generate a checklist file at `FEATURE_DIR/checklists/requirements.md` using the checklist template structure with these validation items:

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
   - [ ] Success criteria are technology-agnostic (no implementation details)
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

   * All items should initially remain **unchecked**. Do **not** attempt to automatically decide which items are satisfied at this stage.
   * Do **not** run an internal validation loop here. The checklist is a contract for later clarification and validation steps, not something `/speckit.specify` must fully satisfy.
   * Clarifications and checklist completion will be handled by:

     * `/speckit.clarify` (interactive clarification and incremental spec updates)
     * Human operators and `scripts/validate_spec.sh` (harness-level quality gate)

7. Report completion with:

   * `BRANCH_NAME`
   * `SPEC_FILE` path
   * `FEATURE_DIR/checklists/requirements.md` path
   * A note that the feature spec is ready for the clarification phase (`/speckit.clarify`) and subsequent planning (`/speckit.plan`).

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## General Guidelines

## Quick Guidelines

* Focus on **WHAT** users need and **WHY**.
* Avoid HOW to implement (no tech stack, APIs, code structure).
* Written for business stakeholders, not developers.
* DO NOT create any checklists that are embedded in the spec. That will be a separate file under `checklists/`.

### Section Requirements

* **Mandatory sections**: Must be completed for every feature
* **Optional sections**: Include only when relevant to the feature
* When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation

When creating this spec from a user prompt:

1. **Make informed guesses**: Use context, industry standards, and common patterns to fill gaps

2. **Document assumptions**: Record reasonable defaults in the Assumptions section

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
