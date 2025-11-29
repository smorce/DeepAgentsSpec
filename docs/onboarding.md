# Onboarding: 長期稼働型 AI エージェント リポジトリの歩き方

このドキュメントは、新規メンバーおよび AI コーディングエージェントが、このリポジトリで作業を開始するときのガイドです。  
リポジトリ全体の概要や用語の定義は `README.md` を参照し、このドキュメントでは「どう作業するか」にフォーカスします。

---

## 1. 最上位レイアウト（全体構成）

リポジトリルートからの構成：

```text
project-root/
├── PLANS.md                # ExecPlan のルールと骨子（これに必ず従うこと）
├── README.md               # プロジェクト概要 / トップページ
│
├── architecture/           # システムレベルのアーキテクチャドキュメント
├── harness/                # 横断的なメタデータとハーネス用スクリプト
├── plans/                  # エピックおよび機能レベルの仕様書
├── services/               # マイクロサービスの実装
├── templates/              # 生成プロンプトやひな型
├── tests/                  # E2Eおよびシステムレベルのテスト
├── scripts/                # リポジトリ全体のヘルパースクリプト
└── docs/                   # オンボーディング、決定事項インデックス、運用情報（このファイルを含む）
````

### 1.1 `harness/`

```text
harness/
├── init.sh                 # リポジトリ全体の初期化 / スモークテスト用スクリプト
├── AI-Agent-progress.txt   # セッション横断の進捗ログ（人間可読）
├── feature_list.json       # エピック／フィーチャのマスタ + spec/ExecPlan パスの対応表
└── harness-config.yaml     # ハーネス設定（サービスリスト、スクリプトパスなど）
```

* `AI-Agent-progress.txt` は **中央ログ** です。
  「いつ・何が起きたか」を全リポジトリ横断で追うための時間軸ログ。

* `feature_list.json` は以下を追跡します：
  * エピック（EPIC-*** ID）とそれに対応する ExecPlan のパス。
  * 機能（F-*** ID）とそれに対応する spec/checklist のパス。

### 1.2 `plans/` (エピックと機能)

```text
plans/
  README.md                             # plans/specs/ExecPlans のワークフローと使用ルール

  system/
    EPIC-SYS-001-foundation/
      exec-plan.md                      # このシステムレベルエピックの ExecPlan
      features/
        F-SYS-001/
          spec.md                       # 機能レベルの仕様書（機能ごと）
          checklists/
            requirements.md             # 仕様品質チェックリスト

  services/
    api-gateway/
      EPIC-API-001-routing/
        exec-plan.md
        features/
          F-API-001/
            spec.md
            checklists/
              requirements.md

    user-service/
      EPIC-USER-001-onboarding/
        exec-plan.md
        features/
          F-USER-001/
            spec.md
            checklists/
              requirements.md
          F-USER-002/
            spec.md
            checklists/
              requirements.md

    billing-service/
      EPIC-BILL-001-invoice/
        exec-plan.md
        features/
          ... (将来の F-BILL-*** 機能)
```

**重要な規約:**

* **ExecPlan**: エピックごとに1つ、常に以下の場所に配置されます：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/exec-plan.md
  ```

* **Feature spec (機能仕様書)**: 機能ごとに1つ、常に以下の場所に配置されます：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/spec.md
  ```

* **Spec checklist (仕様チェックリスト)**: 機能ごとに1つ、常に以下の場所に配置されます：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/checklists/requirements.md
  ```

これらのパスの**信頼できる情報源（Source of Truth）**は `harness/feature_list.json` です。

### 1.3 `services/`, `tests/`, `scripts/`, `docs/` (概要)

* `services/*/` — 各マイクロサービス（ソース、テスト、スクリプト、Dockerfile、設定）。

* `tests/e2e/` — サービス横断的な E2E シナリオとヘルパー。

* `scripts/` — 共有スクリプト。
  この設計における重要なスクリプト：

  ```text
  scripts/validate_spec.sh   # 仕様品質チェックリスト・バリデータ
  ```

* `docs/` — 人間およびエージェント向けのオンボーディング、運用情報、決定事項インデックス。
  この `docs/onboarding.md` は、その中でも「最初に読むべきガイド」です。

---

## 2. コアコンセプト（エピックと機能）

### 2.1 エピック (EPIC-***)

* **大きな作業単位**です（例：「ユーザーオンボーディングフロー」）。

* 正確に1つの ExecPlan を持ちます：

  ```text
  plans/.../<EPIC-ID>/exec-plan.md
  ```

* `features/` 配下に複数の **機能 (features)** を持つことができます。

`harness/feature_list.json` 内では、エピックは `"epics"` の下に存在します：

```jsonc
{
  "epics": [
    {
      "id": "EPIC-USER-001-ONBOARDING",
      "title": "User onboarding flow",
      "category": "service:user-service",
      "services": ["api-gateway", "user-service"],
      "exec_plan_path": "plans/services/user-service/EPIC-USER-001-onboarding/exec-plan.md"
    }
  ]
}
```

### 2.2 機能 (F-***)

* **ひとつのまとまった動作や、ユーザーにとって意味のある小さな価値**を提供する単位です（例：「サインアップページの基本UI」など、利用者が実際に体験できる機能のひと切れ）。
* 独自の **機能仕様書 (feature spec)** と **品質チェックリスト** を持ちます。
* `epic_id` を介してエピックにリンクされます。

`harness/feature_list.json` 内では、機能は `"features"` の下に存在します：

```jsonc
{
  "features": [
    {
      "id": "F-USER-001",
      "epic_id": "EPIC-USER-001-ONBOARDING",
      "title": "Signup page basic UI",
      "description": "User can open /signup and see the signup form.",
      "services": ["api-gateway"],
      "status": "failing",
      "tags": ["frontend", "user-flow"],
      "spec_path": "plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md",
      "checklist_path": "plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md"
    }
  ]
}
```

* 仕様書は機能単位 (per-feature)、ExecPlan はエピック単位 (per-epic) です。

---

## 3. ExecPlan と PLANS.md

### 3.1 ExecPlan とは？

**ExecPlan** は、初心者がゼロからエピックを実装する方法を正確に伝える、文章主体の自己完結型ドキュメントです。

* 各エピックディレクトリ直下の `exec-plan.md` に存在します。
* `PLANS.md` のルールに正確に従う必要があります。
  * `PLANS.md` とは、AIエージェントが長時間・複雑なタスクを実行するために使われる「実行計画（ExecPlan）」のテンプレート文書です。
* **生きたドキュメント**です：進捗があったり、決定が下されたり、予期せぬ事態が見つかるたびに更新されます。

### 3.2 必須セクション

すべての ExecPlan は、少なくとも以下を**含み、維持しなければなりません**：

* `Purpose / Big Picture` (目的 / 全体像)
* `Related Features / Specs (関連フィーチャ ID 一覧)`
* `Progress` (進捗状況 - チェックボックスとタイムスタンプ付き)
* `Surprises & Discoveries` (驚きと発見)
* `Decision Log` (決定ログ)
* `Outcomes & Retrospective` (結果と振り返り)
* `Context and Orientation` (コンテキストとオリエンテーション)
* `Plan of Work` (作業計画)
* `Concrete Steps` (具体的なステップ)
* `Validation and Acceptance` (検証と受け入れ)
* `Idempotence and Recovery` (冪等性とリカバリ)
* `Artifacts and Notes` (成果物とメモ)
* `Interfaces and Dependencies` (インターフェースと依存関係)

**`Related Features / Specs (関連フィーチャ ID 一覧)`** セクションには以下をリストする必要があります：

* 機能 ID（例：`F-USER-001`）
* 短いタイトル
* 完全な `spec.md` のパス（`harness/feature_list.json` に記載の通り）

これにより、エピックレベルの計画から機能レベルの仕様書への明確なリンクが作成されます。

### 3.3 AIコーディングエージェントによる ExecPlan の使用方法

エピックが割り当てられた場合：

1. この `docs/onboarding.md`（このファイル）を読む。
2. `PLANS.md` を完全に読む。
3. `harness/feature_list.json` で定義されているエピックの `exec-plan.md` を開く。
4. ExecPlan 全体を上から下まで読む。
5. `Plan of Work` (作業計画) と `Concrete Steps` (具体的なステップ) に従い、以下を更新する：
   * `Progress`
   * `Surprises & Discoveries`
   * `Decision Log`
   * `Outcomes & Retrospective`
6. ExecPlan は常に **自己完結的** かつ、現在の作業状態に合わせて最新に保つこと。

---

## 4. 機能仕様書 (Feature Specs) と `/speckit` フロー

機能仕様書は、**2段階のフロー**で作成および改善されます：

1. `/speckit.specify` — 機能仕様書の作成/更新。
2. `/speckit.clarify` — 曖昧さの解決と欠落している決定事項の記入。

> 注: `/speckit.*` コマンドは、このリポジトリではなく、周囲の環境（チャットツールなど）によって提供されます。
> このリポジトリのファイルレイアウトは、ツールがここで説明されている通りに動作することを前提としています。

### 4.1 `/speckit.specify` (機能仕様書の作成 / 更新)

* 入力：自然言語による機能説明（`/speckit.specify` の後のテキスト）。
  何を構築しようとしているのか、そしてなぜ構築しようとしているのかを可能な限り明確に記述してください。この時点では技術スタックに焦点を当てないでください。
* 動作（概念）：

  * ブランチ用の短い名前（2〜4語）を生成（例：`user-onboarding`）。
  * 数値プレフィックス（`N`）を選択し、ブランチ `N-short-name` を作成/チェックアウト。
  * `scripts/bash/create-new-feature.sh` または `scripts/powershell/create-new-feature.ps1` を実行。
  * 以下を作成または更新：

    * その機能用の `spec.md`。
    * その機能用の `checklists/requirements.md`。
  * 正しい場所は `harness/feature_list.json` (`spec_path`, `checklist_path`) から取得されます。

結果として生成されるファイルの例：

```text
plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md
plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
```

仕様書は以下を満たす必要があります：

* 実装の詳細ではなく、**WHAT（何）**と**WHY（なぜ）**に焦点を当てる。
* ユーザーシナリオ、機能要件、成功基準を含める。
* `[NEEDS CLARIFICATION: ...]` マーカーの使用は控えめにする（最大3つ）。

### 4.2 `/speckit.clarify` (要件の明確化、人間主導)

明確化作業は**人間によって手動で実行**されます（完全自動ではありません）：
1. 機能の `spec.md` に `[NEEDS CLARIFICATION: ...]` マーカーがあるか確認する。
2. その機能に対して `/speckit.clarify` を実行する。
3. エージェントが、推奨度と理由をつけて選択肢を提示します。（推奨度：⭐の5段階評価）。質問は最大3つまでとする。選択肢を提示するときは、常に考えられる選択肢を5～7個リストアップし、有力な2～4個に絞り込みます。
4. 人間が回答を選択し、`spec.md` を編集する：
   * 各 `[NEEDS CLARIFICATION: ...]` を、選択した回答に基づいた平易な文章に置き換える。
   * 周囲のテキストを整理する。

`[NEEDS CLARIFICATION]` マーカーがなくなるまで繰り返します。

---

## 5. 仕様品質ゲート (`scripts/validate_spec.sh`)

機能が「計画 / 実装の準備完了」と見なされる前に、**仕様品質チェックリスト (Specification Quality Checklist)** に合格する必要があります。

### 5.1 チェックリストの場所

各機能に対して：

```text
plans/.../<EPIC-ID>/features/<FEATURE-ID>/checklists/requirements.md
```

このファイルは `/speckit.specify` によって作成され、以下のような品質チェック項目が記述されています：
* 実装の詳細が含まれていないこと。
* 要件がテスト可能で曖昧でないこと。
* 成功基準が測定可能で、特定の技術に依存していないこと。
* エッジケースが特定されていること。
* 依存関係と前提条件がリストされていること。

### 5.2 バリデータの実行

リポジトリルートから実行します：

```bash
# すべての機能のチェックリストを検証
scripts/validate_spec.sh

# 特定の機能のみを検証
scripts/validate_spec.sh \
  plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
```

動作：

* 各 `requirements.md` をスキャンして、未チェックの項目 (`- [ ] ...`) がないか確認します。

* 各チェックリストファイルについて、ログエントリを `harness/AI-Agent-progress.txt` に書き込みます：

  * **PASSED (合格)** の例：

    ```text
    [2025-10-01 13:00Z] spec quality check: PASSED
    target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
    ```

  * **FAILED (不合格)** の例：

    ```text
    [2025-10-01 13:00Z] spec quality check: FAILED
    target: plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
    incomplete items:
      - line 23: - [ ] Success criteria are measurable
      - line 31: - [ ] Edge cases are identified
    ```

* 終了コード：

  * `0` — すべてチェック済み（仕様品質ゲート PASSED）。
  * `1` — 少なくとも1つのチェックリストに未チェック項目があるか、ファイルが存在しない。

FAILED の場合：

1. その機能の `spec.md` と `requirements.md` を開く。
2. 仕様書を修正する（欠落している成功基準やエッジケースを追加するなど）。
3. 満たされた各チェックリスト項目を `- [x]` にマークする。
4. パスするまで `scripts/validate_spec.sh` を再実行する。

---

## 6. 推奨ワークフロー

### 6.1 人間向け (プロダクト / テックリード)

**新規または変更された機能**の場合：
1. `harness/feature_list.json` に機能エントリを追加/更新する：
   * `id`, `epic_id`, `title`, `spec_path`, `checklist_path`。
2. 自然言語の説明を添えて `/speckit.specify` を実行する。
3. `/speckit.clarify` を使用して、すべての `[NEEDS CLARIFICATION]` マーカーを解消する。
4. 機能のチェックリストがパスするまで `scripts/validate_spec.sh` を実行する。
5. エピックの `exec-plan.md` の `Related Features / Specs (関連フィーチャ ID 一覧)` にこの機能がリストされていることを確認する。

### 6.2 AIコーディングエージェント向け (実装作業)

エピックが割り当てられた場合：

1. `docs/onboarding.md`（このファイル）を読む。
2. `PLANS.md` を完全にを読む。
3. `harness/feature_list.json` を読み込み、以下を行う：
   * エピックを見つける (`epic_id`, `exec_plan_path`)。
   * 関連する機能とその spec/checklist を確認する。
4. エピックの `exec-plan.md` を開く。
5. `Related Features / Specs` を確認する：
   * 各機能の仕様書が存在し、品質チェック済みであることを確認する。
   * 仕様書やチェックリストが欠落または不完全な場合は、停止してこれをブロッキング課題として表面化させる。
6. ExecPlan に従って実装する：
   * 停止するポイントごとに `Progress` を更新する。
   * 自明でない設計上の選択は `Decision Log` に記録する。
   * 予期しない動作は `Surprises & Discoveries` に記録する。
   * `Validation and Acceptance` の記述に従ってテストを追加・実行する。
7. すべてを **安全、冪等、かつ再現可能** に保つ。

---

## 7. クイックチェックリスト (新しいセッションを開始するエージェント向け)

1. ✅ `docs/onboarding.md`（このファイル）を読む。
2. ✅ `PLANS.md` を読む。
3. ✅ `harness/feature_list.json` を検査して以下を特定する：
   * ターゲットとなるエピック (`epic_id`, `exec_plan_path`)。
   * 関連する機能 (`spec_path`, `checklist_path`)。
4. ✅ 関連する機能仕様書が存在し、`scripts/validate_spec.sh` をパスすることを確認する。
5. ✅ エピックの `exec-plan.md` を開き、すべてのセクションを更新しながらそれに従う。

これらの前提条件のいずれかが欠けている場合、**パスや構造を推測しないでください**。
その代わり、欠落している成果物を `harness/AI-Agent-progress.txt` または ExecPlan の `Progress` / `Surprises & Discoveries` に記録し、人間の入力を待つために停止してください。