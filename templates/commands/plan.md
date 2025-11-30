---
description: Feature-level implementation planning workflow for this long-running AI agent repo. Generates design artifacts colocated with the feature spec and updates the epic-level design index.
handoffs: 
  - label: Create Tasks
    agent: speckit.tasks
    prompt: >
      Break the implementation plan for this feature into tasks, using the IMPL_PLAN and the generated design artifacts
      (research.md, data-model.md, contracts/, quickstart.md).
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: >
      Create an implementation checklist for this feature based on the IMPL_PLAN, research.md, data-model.md,
      contracts/, and quickstart.md. Focus on concrete, verifiable steps that a coding agent can execute.
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup (feature context)**
   From the repo root, run `{SCRIPT}` and parse the JSON output. Expect at least:

   * `FEATURE_SPEC` — path to the feature spec (e.g. `plans/.../features/F-XXX/spec.md`)
   * `IMPL_PLAN` — path to the feature implementation plan (e.g. `plans/.../features/F-XXX/impl-plan.md`)
   * `SPECS_DIR` — directory containing the feature spec (e.g. `plans/.../features/F-XXX`)
   * `BRANCH` — current branch name
   * `HAS_GIT` — `"true"` or `"false"`

   Derive:

   * `FEATURE_CHECKLIST` = `${SPECS_DIR}/checklists/requirements.md`
   * `PLAN_CHECKLIST`    = `${SPECS_DIR}/checklists/PlanQualityGate.md`
   * `FEATURE_ID` as the leaf directory name of `SPECS_DIR` (typically `F-XXX-YYY`)
   * `EPIC_DIR` as the parent directory of the `features` directory that contains `SPECS_DIR`
     (i.e. two levels up from `SPECS_DIR`)
   * `EPIC_DESIGN_INDEX` = `${EPIC_DIR}/design/index.md`

   For single quotes in args like `"I'm Groot"`, use escape syntax: e.g. `'I'\''m Groot'`
   (or double-quote if possible: `"I'm Groot"`).

2. **Spec quality gate (required for this repo)**

   Before changing any plan or generating design artifacts:

   * Verify that `FEATURE_CHECKLIST` exists. If it does not, **STOP** and return an ERROR indicating the missing checklist.

   * From the repo root, run:

     ```bash
     scripts/validate_spec.sh "${FEATURE_CHECKLIST}"
     ```

   * If the script returns a non-zero exit code:

     * Treat this as a **spec quality gate failure**.
     * Do **not** create or modify `IMPL_PLAN` or any design artifacts.
     * Report:

       * The `FEATURE_CHECKLIST` path.
       * The incomplete items from the validator output.
     * Prefer to append a short, timestamped entry to `harness/AI-Agent-progress.txt` indicating the gate failure.

   * Only if the quality gate **passes** may you proceed with the planning workflow.

3. **Load context (feature + epic)**

   * Read `FEATURE_SPEC`.

   * Read `/memory/constitution.md`.

   * Load the IMPL_PLAN template (already copied to `IMPL_PLAN` by the setup script).

   * If `EPIC_DESIGN_INDEX` exists, read it as **epic-level design context**:

     * Shared entities and contracts across multiple features.
     * Cross-feature invariants and constraints.
     * Any prior decisions that affect this feature.

   * If `EPIC_DESIGN_INDEX` does not exist:

     * You may create `${EPIC_DIR}/design/index.md` later in this workflow if you introduce shared concepts.

4. **Execute the feature plan workflow**

   Follow the structure in the `IMPL_PLAN` template to:

   * Fill **Technical Context**:

     * Use `FEATURE_SPEC` and (if present) `EPIC_DESIGN_INDEX` as primary inputs.
     * Mark all unknowns as `NEEDS CLARIFICATION`.

   * Fill **Constitution Check** using `/memory/constitution.md`.

   * Evaluate gates; return an ERROR if any violations are not explicitly justified.

   * **Phase 0**: Generate `${SPECS_DIR}/research.md` and resolve all `NEEDS CLARIFICATION`.

   * **Phase 1**:

     * Generate `${SPECS_DIR}/data-model.md`, `${SPECS_DIR}/contracts/`, and `${SPECS_DIR}/quickstart.md`.
     * Update the epic-level design index at `${EPIC_DESIGN_INDEX}` (create if missing) with:

       * A short entry for this feature (`FEATURE_ID`, title, and links to the design artifacts).
       * Any shared entities / endpoints / invariants that affect other features in the same epic.

   * **Phase 1**: Update agent context by running the appropriate `{AGENT_SCRIPT}`.

   * Re-evaluate the **Constitution Check** after the design artifacts and epic design index have been updated.

5. **Plan quality checklist (PlanQualityGate.md initialization)**

   After the IMPL_PLAN and design artifacts have been brought into a consistent state:

   * Ensure `${SPECS_DIR}/checklists/` exists; create it if missing.

   * If `${PLAN_CHECKLIST}` does **not** exist:

     * Create `${PLAN_CHECKLIST}`.
     * Populate it with the **Plan quality checklist template** defined in
       [Plan quality checklist template (PlanQualityGate.md)](#plan-quality-checklist-template-planmd),
       replacing placeholders (`<FEATURE-ID>`, `<EPIC-ID>`, `<scope>`, etc.) with actual values for this feature.

   * If `${PLAN_CHECKLIST}` **already exists`**:

     * Do **not** overwrite it wholesale.
     * You may normalize headings or append missing sections from the template,
       but you must preserve any existing check states (`- [x]` / `- [ ]`).

   * The Plan quality gate is designed to validate this `${PLAN_CHECKLIST}` with `scripts/validate_plan.sh` or similar.
     The responsibility of `/speckit.plan` execution is to "prepare the skeleton";
     filling in the checks is done by humans or subsequent agents.

6. **Stop and report**

   The command ends after Phase 2 planning (as defined by the IMPL_PLAN template). Report:

   * `BRANCH`

   * `IMPL_PLAN` path

   * Generated feature-level artifacts:

     * `${SPECS_DIR}/research.md`
     * `${SPECS_DIR}/data-model.md`
     * `${SPECS_DIR}/contracts/`
     * `${SPECS_DIR}/quickstart.md`
     * `${PLAN_CHECKLIST}` (if created or updated)

   * Epic-level artifact (if touched or created):

     * `${EPIC_DESIGN_INDEX}`

   Optionally append a summary entry to `harness/AI-Agent-progress.txt`.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** in `IMPL_PLAN`:

   * For each `NEEDS CLARIFICATION` → research task.
   * For each dependency → best practices task.
   * For each integration (across services or features) → patterns task.

2. **Generate and dispatch research agents** (via speckit or an equivalent mechanism):

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for the feature described in FEATURE_SPEC within this repo"

   For each technology choice:
     Task: "Find best practices for {tech} in {domain} within the constraints of this repo and its architecture"
   ```

   * When the epic-level design index exists, prefer patterns and decisions that are consistent with it.
   * If research suggests changing a prior epic-level decision, make sure:

     * The change is explicit.
     * The rationale is recorded in both `research.md` and the ExecPlan’s Decision Log.

3. **Consolidate findings** in `${SPECS_DIR}/research.md` using the format:

   * Decision: [what was chosen]
   * Rationale: [why it was chosen]
   * Alternatives considered: [what else was evaluated]

**Output**: `${SPECS_DIR}/research.md` with all `NEEDS CLARIFICATION` resolved for this feature.

### Phase 1: Design & Contracts

**Prerequisites:** `${SPECS_DIR}/research.md` is complete and consistent with:

* The `IMPL_PLAN`
* The feature spec (`FEATURE_SPEC`)
* The epic-level design index (if it exists)

1. **Extract entities from the feature spec** into `${SPECS_DIR}/data-model.md`:

   * Entity names, fields, and relationships.

   * Validation rules derived from:

     * `FEATURE_SPEC`
     * `requirements.md` (the spec checklist)

   * State transitions, if applicable (e.g. signup → email_verified).

2. **Generate API contracts** from functional requirements:

   * For each user-visible action or interaction → define one endpoint or mutation.
   * Use REST/GraphQL patterns consistent with existing services in this repo.
   * Output OpenAPI/GraphQL schema files into `${SPECS_DIR}/contracts/`.
   * When an endpoint or entity is shared across multiple features in the same epic:

     * Make that explicit in the epic design index (see step 4).

3. **Create quickstart for implementers** in `${SPECS_DIR}/quickstart.md`:

   * Where the implementation is expected to live (services, modules, packages).
   * How to run and test the new behaviour (unit, integration, e2e).
   * Any assumptions or invariants that implementers must respect.
   * Links to:

     * `FEATURE_SPEC`
     * `requirements.md`
     * `research.md`
     * `data-model.md`
     * `contracts/`

4. **Update epic-level design index (`EPIC_DESIGN_INDEX`)**:

   * Ensure `${EPIC_DIR}/design/` exists; create it if missing.

   * Create or update `${EPIC_DESIGN_INDEX}` to include:

     * A short entry for this feature:

       * `FEATURE_ID`
       * Short title
       * Single-sentence summary of the behaviour
       * Links (relative paths from repo root) to:

         * `FEATURE_SPEC`
         * `${SPECS_DIR}/data-model.md`
         * `${SPECS_DIR}/contracts/`
         * `${SPECS_DIR}/quickstart.md`

     * Any cross-feature elements:

       * Shared entities and their owning feature.
       * Shared endpoints / routes.
       * Cross-feature invariants or sequencing (e.g. “F-001 must run before F-002”).

   * Keep `index.md` **lightweight**:

     * It should function as a map and index, not a full copy of each feature’s design.

5. **Agent context update**:

   * From the repo root, run `{AGENT_SCRIPT}`:

     * The script detects which AI agent is in use.
     * It updates the appropriate agent-specific context file.
     * It adds only new technologies, patterns, or cross-feature design elements introduced by this plan.
     * It preserves manual additions between markers.

**Output**:

* `${SPECS_DIR}/data-model.md`
* `${SPECS_DIR}/contracts/*`
* `${SPECS_DIR}/quickstart.md`
* Updated `${EPIC_DESIGN_INDEX}`
* Updated agent-specific context file

---

## Plan quality checklist template (PlanQualityGate.md)

When creating `${PLAN_CHECKLIST}` for the first time, use the following skeleton.
Replace placeholders such as `<FEATURE-ID>`, `<EPIC-ID>`, `<scope>` with concrete values.

```markdown
# Plan Quality Checklist: <FEATURE-ID>

対象フィーチャ:
- ID: <FEATURE-ID>
- Epic: <EPIC-ID>
- Impl plan: `plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/impl-plan.md`

## A. Plan 本体の構造

- [ ] `impl-plan.md` が存在し、この FEATURE-ID と対応する spec へのリンクが明記されている。
- [ ] 必須セクション（Summary / Technical Context / Constitution Check / Project Structure / Complexity Tracking）が埋まっており、ダミーや空欄が残っていない。
- [ ] `impl-plan.md` 内に `NEEDS CLARIFICATION` 相当のプレースホルダが残っていない。

## B. Technical Context / Constitution Check

- [ ] Technical Context の各項目が、このフィーチャの実際の実装方針を具体的に表している。
- [ ] Constitution Check に適用するゲート条件と、その満たし方が記述されている。
- [ ] 満たせないゲートがある場合、Complexity Tracking に理由と却下した代替案が明記されている。

## C. プロジェクト構造 / 影響範囲

- [ ] 採用する Project Structure が 1 つだけ選ばれており、不要なテンプレート構造が削除されている。
- [ ] 列挙されたディレクトリ/ファイルパスがリポジトリルートからの正しいパスである。
- [ ] このフィーチャが触る既存モジュールやサービスの位置と役割が明記されている。

## D. 研究・設計成果物との整合性

- [ ] `research.md` が存在し、主要な不明点ごとに「Decision / Rationale / Alternatives considered」が書かれている。
- [ ] `data-model.md` が存在し、このフィーチャが扱うエンティティ・フィールド・関係・バリデーションルールが列挙されている。
- [ ] `contracts/` 配下に、このフィーチャで追加・変更される契約が置かれている（形式はプロジェクト標準に従う）。
- [ ] `quickstart.md` が存在し、このフィーチャだけを試す手順が書かれている。
- [ ] `impl-plan.md` と `research.md` / `data-model.md` / `contracts/` / `quickstart.md` の内容が矛盾していない。

## E. Epic design index / 他フィーチャとの関係

- [ ] エピック配下に `design/index.md` が存在する場合、`impl-plan.md` の Artifacts/Notes からそのパスと役割が参照されている。
- [ ] 共有エンティティや共有 API がある場合、その所有者と他フィーチャとの関係が `design/index.md` または `impl-plan.md` のいずれかで明示されている。

## F. Plan から Tasks へのブレイクダウン準備

- [ ] Plan of Work / Concrete Steps を読むだけで、`/speckit.tasks` が「どのファイルにどのような変更タスクを切るか」を機械的に列挙できる具体性になっている。
- [ ] Validation / Acceptance に、この Plan 完了時の具体的な成功条件（コマンド・HTTP リクエストなど）が書かれている。
- [ ] Idempotence / Recovery に、途中失敗時のやり直しや既存環境への影響最小化方針が触れられている。
```

---

## Key rules

* Use paths that are absolute from the **repo root** (e.g. `plans/...`, `services/...`, `scripts/...`), not `./` or `../`.

* Treat `FEATURE_SPEC` and `requirements.md` as the **source of truth** for feature behaviour; this plan must not override them.

* Do **not** proceed past Phase 0/1 if:

  * Any `NEEDS CLARIFICATION` remains unresolved, or
  * The spec quality gate fails, or
  * Constitution checks fail without explicit, written justification.

* Keep `${EPIC_DESIGN_INDEX}` focused on **cross-feature context** and pointers:

  * Avoid duplicating full content of feature-level artifacts.
  * Use short summaries and links instead.

* Ensure `${PLAN_CHECKLIST}` exists and follows the provided template before handing off to `/speckit.tasks` or any Task quality gate.

* When a major gate passes or fails, prefer to log a short, timestamped line in `harness/AI-Agent-progress.txt`.