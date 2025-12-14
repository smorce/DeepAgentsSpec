# ExecPlan / Feature Spec ワークフロー

このリポジトリでは、機能仕様書 (Feature spec) と実行計画書 (ExecPlan) を、リンクされているが別個の成果物として扱います。

- **Feature spec (機能仕様書)**: 機能ごと、ユーザー向けの要件 (`features/F-XXX-YYY/` 配下の `spec.md`)
- **ExecPlan (実行計画書)**: エピックごと、実装計画 (`EPIC-XXX-YYY/` 配下の `exec-plan.md`)

Feature spec は `/speckit.specify` → `/speckit.clarify` フローを通じて作成・洗練され、ExecPlan を作成または更新する前に、必ず仕様品質チェック (spec quality check) に合格する必要があります。

## 1. Feature Spec の作成 / 更新 (`/speckit.specify`)

1.  speckit が有効な環境 (チャットまたは CLI) で、作りたいアプリ/機能の自然言語説明とともに `/speckit.specify` を実行します。`/speckit.specify` の後ろのテキストがそのまま入力になります（Feature ID 指定は不要）。

2.  `/speckit.specify` は以下を自動で行います:
    -   入力をエピック/フィーチャに分割し、`harness/feature_list.json` を新規作成または更新。
    -   付番したエピックID/フィーチャIDに基づき、以下に Feature spec を初期化・記入:
        -   `plans/<scope>/<service>/<EPIC-ID>/features/<FEATURE-ID>/spec.md`
    -   併せて品質チェックリストを作成:
        -   `plans/<scope>/<service>/<EPIC-ID>/features/<FEATURE-ID>/checklists/requirements.md`

4.  生成された `spec.md` を必要に応じて編集し、**ユーザー/ビジネス**の視点から機能をより適切に反映させます。
    -   実装の詳細 (言語、フレームワーク、内部 API) は追加しないでください。
    -   `[NEEDS CLARIFICATION: ...]` は、本当に進行を妨げる不確実な点 (仕様ごとに最大 3 つまで) にのみ使用してください。

## 2. 要件の明確化 (`/speckit.clarify` — 手動主導)

clarify (明確化) ステップは、**人間のオペレーターによって手動で**実行されます。エージェントが質問を提案し、人間が回答を決定して仕様に適用します。

1.  ターゲット機能の Feature spec ファイルを開きます。例えば:
    -   `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md`

    `[NEEDS CLARIFICATION: ...]` マーカーを探します。

2.  その機能に対して `/speckit.clarify` を実行します。
    clarify フローは以下を実行します:
    -   仕様から最大 3 つの影響の大きい明確化ポイントを収集します。
    -   それぞれを、短いコンテキストの引用と提案された回答の表 (A/B/C/Custom) と共に質問として提示します。

3.  人間のオペレーターとして:
    -   すべての質問 (Q1, Q2, Q3) を読みます。
    -   回答を決定します。例えば:
        -   `Q1: A`
        -   `Q2: Custom - [独自の記述]`
        -   `Q3: B`
    -   これらの回答を**直接仕様ファイルに適用**します:
        -   各 `[NEEDS CLARIFICATION: ...]` マーカーを、選択した回答 (通常の文章) に置き換えます。
        -   仕様が自然で一貫性を持って読めるように、周囲のテキストを調整します。

4.  必要に応じて、以下のような状態になるまで `/speckit.clarify` を繰り返します:
    -   `spec.md` に `[NEEDS CLARIFICATION]` マーカーが残っていない。
    -   仕様が一貫しており、機能レベルでテスト可能である。

この時点で、Feature spec は論理的には明確化されていますが、まだ品質ゲートを通過していません。

## 3. Spec 品質チェックの実行 (Harness quality gate)

計画 (`/speckit.plan`) に進む前、または ExecPlan を記述/更新する前に、仕様品質チェックリスト (Specification Quality Checklist) に合格する必要があります。

1.  リポジトリのルートから、ターゲット機能の検証スクリプトを実行します:

    ```bash
    # F-USER-001 の例
    scripts/validate_spec.sh \
      plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
    ```

    引数を省略した場合、スクリプトは `plans/**/features/**/checklists/requirements.md` 配下の**すべて**の機能チェックリストをスキャンします。

2.  スクリプトは以下を実行します:
    -   チェックリスト内の未チェック項目 (`- [ ] ...`) を探します。
    -   `harness/AI-Agent-progress.txt` に以下のいずれかの形式でログエントリを追加します:

        -   PASSED (合格):

            ```text
            [2025-10-01 13:00Z] spec quality check: PASSED
            target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
            ```

        -   FAILED (不合格 - 未完了項目の箇条書き付き):

            ```text
            [2025-10-01 13:00Z] spec quality check: FAILED
            target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
            incomplete items:
              - line 23: - [ ] Success criteria are measurable
              - line 31: - [ ] Edge cases are identified
            ```

    -   終了ステータス:
        -   すべての項目がチェックされている場合 (`- [ ]` 行が残っていない場合) は `0`。
        -   未チェック項目やチェックリストの欠落が見つかった場合は `1`。

3.  スクリプトが FAILED を報告した場合:
    -   対応する `requirements.md` を開きます。
    -   未チェック項目ごとに、Feature spec (`spec.md`) を適切に更新し、チェックリスト項目をチェック済み (`- [x]`) にマークします。
    -   PASSED が報告されるまで `scripts/validate_spec.sh` を再実行します。

## 4. Spec の準備完了後

Feature spec が以下の状態になったら:

-   `[NEEDS CLARIFICATION]` マーカーがない。
-   完全にチェックされた仕様品質チェックリストがある (`validate_spec.sh` が PASSED を報告する)。

以下に進むことができます:

-   対応するエピックの ExecPlan (`EPIC-XXX-YYY/` 配下の `exec-plan.md`) を作成または更新する。
-   ExecPlan の `Related Features / Specs (関連フィーチャ ID 一覧)` セクションに、以下を使用して機能をリストする:
    -   機能 ID (例: `F-USER-001`)
    -   `harness/feature_list.json` からの spec パス
    -   短いタイトル

> **Quick recipe (人がやる手順のざっくり版)**
>
> 1.  `/speckit.specify` でフィーチャ仕様（spec.md + checklist）を作る
> 2.  `/speckit.clarify` の質問に答えながら spec.md を手で直し、`[NEEDS CLARIFICATION]` を消す
> 3.  `scripts/validate_spec.sh` を通して checklist の未チェック項目をゼロにする
> 4.  そのフィーチャをカバーする ExecPlan（`exec-plan.md`）を作成・更新する
