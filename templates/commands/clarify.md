---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs: 
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
scripts:
   sh: scripts/bash/check-prerequisites.sh --json --paths-only
   ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
````

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

This clarification workflow is expected to run (and be completed) **BEFORE** invoking `/speckit.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Clarify operates on two inputs:

1. Explicit `[NEEDS CLARIFICATION: ...]` markers produced by `/speckit.specify`.
2. Implicit ambiguities detected via a structured taxonomy scan.

Both are allowed. Explicit markers are always treated as **higher priority** than implicit taxonomy findings.

Execution steps:

1. Run `{SCRIPT}` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:

   * `FEATURE_DIR`
   * `FEATURE_SPEC`
   * (Optionally capture `IMPL_PLAN`, `TASKS` for future chained flows.)
   * If JSON parsing fails, abort and instruct user to re-run `/speckit.specify` or verify feature branch environment.
   * For single quotes in args like "I'm Groot", use escape syntax: e.g. `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`).

2. Load the current spec file and build an **ambiguity and coverage map** from two sources:

   1. **Explicit markers**:

      * Scan the spec for occurrences of `[NEEDS CLARIFICATION: ...]`.
      * For each marker, capture:

        * The full marker text.
        * The surrounding sentence/paragraph and section heading.
        * A short topic label inferred from the marker text (e.g., "signup flow edge cases", "role permissions").
      * Treat these as **high-priority candidate questions**.

   2. **Taxonomy-based scan** (implicit ambiguities):

      Use the following taxonomy to evaluate coverage. For each category, mark status: Clear / Partial / Missing, based on the content of the spec **excluding what is already covered by explicit markers**.

      Functional Scope & Behavior:

      * Core user goals & success criteria
      * Explicit out-of-scope declarations
      * User roles / personas differentiation

      Domain & Data Model:

      * Entities, attributes, relationships
      * Identity & uniqueness rules
      * Lifecycle/state transitions
      * Data volume / scale assumptions

      Interaction & UX Flow:

      * Critical user journeys / sequences
      * Error/empty/loading states
      * Accessibility or localization notes

      Non-Functional Quality Attributes:

      * Performance (latency, throughput targets)
      * Scalability (horizontal/vertical, limits)
      * Reliability & availability (uptime, recovery expectations)
      * Observability (logging, metrics, tracing signals)
      * Security & privacy (authN/Z, data protection, threat assumptions)
      * Compliance / regulatory constraints (if any)

      Integration & External Dependencies:

      * External services/APIs and failure modes
      * Data import/export formats
      * Protocol/versioning assumptions

      Edge Cases & Failure Handling:

      * Negative scenarios
      * Rate limiting / throttling
      * Conflict resolution (e.g., concurrent edits)

      Constraints & Tradeoffs:

      * Technical constraints (language, storage, hosting)
      * Explicit tradeoffs or rejected alternatives

      Terminology & Consistency:

      * Canonical glossary terms
      * Avoided synonyms / deprecated terms

      Completion Signals:

      * Acceptance criteria testability
      * Measurable Definition of Done style indicators

      Misc / Placeholders:

      * TODO markers / unresolved decisions
      * Ambiguous adjectives ("robust", "intuitive") lacking quantification

      For each category with Partial or Missing status, add a candidate question opportunity unless:

      * Clarification would not materially change implementation or validation strategy.
      * Information is better deferred to planning phase (note internally).

   Maintain this as an internal coverage map used for prioritization. Do not output the raw map unless no questions will be asked.

3. Build a prioritized queue of candidate clarification questions (maximum 5 per session):

   * Start from **explicit `[NEEDS CLARIFICATION]` markers**:

     * For each marker, derive **exactly one** focused question that, when answered, lets you either:

       * Replace that marker with concrete text, or
       * Rewrite the surrounding requirement/scenario to be testable.
   * Then, if capacity remains, add high-impact taxonomy-based questions:

     * Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
   * Apply these global constraints:

     * Maximum of 5 questions in this run.
     * Maximum of 10 total questions across the whole conversation/session.
     * Each question must be answerable with EITHER:

       * A short multiple-choice selection (2–5 distinct, mutually exclusive options), OR
       * A one-word / short-phrase answer (explicitly constrain: "Answer in <=5 words").
   * Prioritization:

     * Always prefer:

       1. Explicit `[NEEDS CLARIFICATION]` markers (sorted by impact: scope > security/privacy > user experience > technical details).
       2. Highest-impact unresolved taxonomy categories (using an Impact × Uncertainty heuristic).
     * Exclude:

       * Questions already answered in the spec.
       * Trivial stylistic preferences.
       * Plan-level execution details (unless blocking correctness).
   * If more than 5 candidate questions remain after prioritization, keep only the top 5 and mark the rest as Deferred in the final coverage summary.

4. Sequential questioning loop (interactive):

   For each question in the queue, follow this pattern.

   ### 4.1 Explain the decision first

   - Before showing any options, briefly explain:
     - **What problem / ambiguity this question is trying to resolve**, and
     - **Why it matters** (e.g., scope impact, security risk, UX behavior, data model stability, operational risk).
   - Keep this explanation to 1–2 sentences so the user understands the context of the decision.

   ### 4.2 Multiple-choice questions (with recommendation and star ratings)

   - When the question can be expressed as discrete alternatives, you MUST:

     1. **Internally enumerate 5–7 plausible options** that are:
        - Mutually exclusive in practice (the user should normally pick just one).
        - Realistic for this project’s domain and constraints.

     2. For each option:
        - Evaluate its suitability.
        - Assign a **recommendation score** using a **1–5 ⭐ rating**:
          - ⭐⭐⭐⭐⭐ — strongly recommended (best overall)
          - ⭐⭐⭐⭐ — recommended (very good, minor tradeoffs)
          - ⭐⭐⭐ — acceptable but with notable tradeoffs
          - ⭐⭐ — weak option, not recommended unless explicitly needed
          - ⭐ — generally undesirable

     3. From the 5–7 options, identify **2–4 “strong candidates”** (usually those with ⭐⭐⭐⭐ or ⭐⭐⭐⭐⭐).
        - There must be at least one clear **top recommendation**.

     4. Present the results to the user in this order:

        - First, a one-line summary of the top recommendation:

          `**Recommended:** Option [X] (⭐⭐⭐⭐⭐ or ⭐⭐⭐⭐) - <1–2 sentence reasoning>`

        - Then, a Markdown table listing **all 5–7 options**, each with:
          - Option letter (A–G).
          - Short answer / label.
          - Star rating (⭐1–5).
          - Short justification (why you rated it that way).

        Suggested table format:

        | Option | Answer                                   | Recommendation | Rationale                                  |
        |--------|------------------------------------------|----------------|--------------------------------------------|
        | A      | <Option A description>                  | ⭐⭐⭐⭐          | <Why this is a strong candidate>          |
        | B      | <Option B description>                  | ⭐⭐⭐⭐⭐         | <Why this is likely the best choice>      |
        | C      | <Option C description>                  | ⭐⭐⭐           | <Tradeoffs / when this might be chosen>   |
        | D      | <Option D description>                  | ⭐⭐            | <Why this is weaker>                      |
        | E      | <Option E description>                  | ⭐             | <Why this is generally undesirable>       |
        | Short  | Provide a different short answer (<=5 words) | —        | For a custom answer not listed above      |

        - You MUST keep the total number of options (including `Short`) between **5 and 7**.
        - Among them, clearly indicate which 2–4 are “strong candidates” (e.g., ⭐⭐⭐⭐ or ⭐⭐⭐⭐⭐).

     5. After the table, always add this instruction:

        `You can reply with the option letter (e.g., "A"), accept the recommended option by saying "yes" or "recommended", or provide your own short answer (<=5 words).`

   ### 4.3 Short-answer style questions (no meaningful discrete options)

   - If the ambiguity cannot be expressed as a small set of discrete options (for example, a short label, a threshold value, or a brief naming choice), you MAY use a constrained short-answer format instead.

   - In that case:

     1. Propose a **suggested answer** based on best practices and context.

        Format:

        `**Suggested:** <your proposed answer> - <brief reasoning>`

     2. Explicitly constrain the response:

        `Format: Short answer (<=5 words). You can accept the suggestion by saying "yes" or "suggested", or provide your own answer.`

   ### 4.4 Handling the user’s reply

   - After the user answers:

     - If the user replies with `"yes"`, `"recommended"`, or `"suggested"`,  
       → Use your previously stated recommended/suggested answer as the final answer.

     - If the user replies with an option letter (`"A"`, `"B"`, …),  
       → Map it to the corresponding option row in the table and use that row’s answer.

     - If the user provides a custom short answer:
       - Ensure it fits the `<= 5 words` constraint.
       - If it is ambiguous or partially overlaps multiple options, ask for a **very brief** disambiguation (this still counts as the same question; do not increase the question counter).

   - Once a satisfactory answer is obtained:
     - Record it in working memory for that question.
     - Proceed to the next question in the queue.

   - Stop asking further questions when:
     - All critical ambiguities are resolved early (remaining queued items become unnecessary), OR
     - The user signals completion ("done", "good", "no more"), OR
     - You reach 5 asked questions in this run.

   - Never reveal future queued questions in advance.
   - If no valid questions exist at start, immediately report that no critical ambiguities were found (see step 8).

5. Integration after EACH accepted answer (incremental update approach):

   * Maintain an in-memory representation of the spec (loaded once at start) plus the raw file contents.

   * For each accepted answer:

     1. **If tied to a `[NEEDS CLARIFICATION]` marker**:

        * Locate the corresponding marker instance in the spec.
        * Rewrite the surrounding sentence/paragraph to integrate the answer in natural prose.
        * Remove the `[NEEDS CLARIFICATION: ...]` text entirely.
        * When appropriate, also update the closest structured section:

          * Functional ambiguity → update Functional Requirements / User Scenarios.
          * UX ambiguity → update User Scenarios / Interaction Flow.
          * Data ambiguity → update Data Model / Entities.
          * Non-functional → update Success Criteria / Non-functional constraints.
          * Edge case → update Edge Cases / Error Handling.

     2. **If derived purely from taxonomy (no explicit marker)**:

        * Identify the most relevant section based on the category:

          * Functional Scope & Behavior → Functional Requirements / User Scenarios.
          * Domain & Data Model → Entities / Attributes / Relationships.
          * UX Flow → User Journeys / Interaction sections.
          * Non-Functional → Quality / Success Criteria sections.
          * Edge Cases → Edge Cases / Failure Handling.
          * Constraints & Tradeoffs → Constraints / Assumptions.
        * Insert or adjust content so that the answer becomes:

          * Concrete.
          * Testable.
          * Clearly associated with the right part of the spec.

   * When integrating, follow these rules:

     * If the clarification **invalidates** an earlier ambiguous statement, replace that statement instead of duplicating it.
     * Do not leave obsolete or contradictory text.
     * Preserve overall formatting:

       * Do not reorder unrelated sections.
       * Keep heading hierarchy intact.
     * Keep each inserted clarification minimal and testable (avoid narrative drift).

   * Save the spec file AFTER each integration to minimize risk of context loss (atomic overwrite).

   * **Important**: Do **NOT** introduce a new `## Clarifications` section.
     All clarifications must be reflected directly in the existing sections (Functional Requirements, Data Model, Success Criteria, Edge Cases, etc.). The spec should read as if it had been written correctly the first time.

6. Validation (after EACH write plus a final pass):

   * For every question you prompted and answer you accepted:

     * Confirm that the corresponding ambiguity in the spec is resolved:

       * The relevant `[NEEDS CLARIFICATION]` marker (if any) is removed.
       * The updated requirement / scenario / constraint is concrete and testable.
   * Confirm that:

     * Total asked (accepted) questions in this run ≤ 5.
     * No newly added vague placeholders (e.g., "robust", "intuitive") were introduced as part of the answer.
     * No contradictory earlier statement remains (scan for now-invalid alternative choices and adjust).
   * It is acceptable for **other** `[NEEDS CLARIFICATION]` markers to remain if they were:

     * Not selected as high-priority in this run, or
     * Explicitly deferred by the user.
       These will be surfaced later by humans and/or `scripts/validate_spec.sh`.

7. Write the updated spec back to `FEATURE_SPEC`.

8. Report completion (after questioning loop ends or early termination):

   Your final response (in the clarification session) must include:

   * Number of questions asked & answered in this run.

   * Path to updated spec (`FEATURE_SPEC`).

   * Sections that were touched (list by heading name).

   * Count and short description of:

     * Resolved explicit `[NEEDS CLARIFICATION]` markers.
     * Remaining explicit `[NEEDS CLARIFICATION]` markers (if any).

   * A **coverage summary** table listing each taxonomy category with Status and Notes:

     * Status values:

       * Resolved — was Partial/Missing and addressed in this run.
       * Deferred — still Partial/Missing but not addressed due to quota, user choice, or low immediate priority.
       * Clear — already sufficiently covered.
       * Outstanding — still Partial/Missing but judged low-impact for now.

   * A recommendation for next steps:

     * Whether it is reasonable to proceed to `/speckit.plan` now, **and**
     * Whether the user should run `scripts/validate_spec.sh` for this feature to enforce the checklist gate.

   Example recommendation language:

   * "Spec is now sufficiently clarified for planning. Please run `scripts/validate_spec.sh <checklist-path>` before relying on it as a hard gate."
   * "Several high-impact areas remain Deferred or Outstanding. Consider another `/speckit.clarify` pass or manual edits before `/speckit.plan`."

Behavior rules:

* If no meaningful ambiguities are found (and there are no `[NEEDS CLARIFICATION]` markers, or all are clearly low impact), respond:

  > "No critical ambiguities detected worth formal clarification."

  and provide a compact coverage summary (all categories Clear or low-impact Deferred), then suggest proceeding.

* If the spec file is missing, instruct the user to run `/speckit.specify` first (do not create a new spec here).

* Never exceed 5 total asked questions in a single clarification run (clarification retries for a single question do not count as new questions).

* Avoid speculative tech stack questions unless the absence blocks functional clarity.

* Respect user early termination signals ("stop", "done", "proceed").

* If the quota is reached with unresolved high-impact categories remaining, explicitly flag them under Deferred with rationale.

* Treat `/speckit.clarify` as a **preparation step**: it makes `/speckit.plan` and ExecPlans safer and cheaper, but ultimate readiness is enforced by humans + `scripts/validate_spec.sh`.