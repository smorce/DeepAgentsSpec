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
├── plans/                  # エピックおよび機能レベルの仕様書 + エピック設計インデックス
├── services/               # マイクロサービスの実装
├── templates/              # 生成プロンプトやひな型
├── tests/                  # E2Eおよびシステムレベルのテスト
├── scripts/                # リポジトリ全体のヘルパースクリプト
└── docs/                   # オンボーディング、決定事項インデックス、運用情報（このファイルを含む）
```

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
      design/
        index.md                        # システムレベルエピックの設計インデックス（サービス横断の地図）
      # NOTE: system 配下には通常 features/ は作りません。
      # 実際の機能（コードに直結する単位）は services/ 配下のエピックで管理します。

  services/
    api-gateway/
      EPIC-API-001-routing/
        exec-plan.md                    # サービスレベルエピックの ExecPlan
        design/
          index.md                      # エピック内の設計インデックス（複数フィーチャの横断的な地図）
        features/
          F-API-001/
            spec.md                     # 機能レベルの仕様書（機能ごと）
            impl-plan.md                # この機能の実装計画（/speckit.plan から生成）
            research.md                 # この機能向けのリサーチ結果（Phase 0）
            data-model.md               # この機能が扱うデータモデル（Phase 1）
            contracts/                  # この機能に紐づく API 契約（Phase 1）
            quickstart.md               # 実装者向けのクイックスタート（Phase 1）
            checklists/
              requirements.md           # 仕様品質チェックリスト

    user-service/
      EPIC-USER-001-onboarding/
        exec-plan.md
        design/
          index.md
        features/
          F-USER-001/
            spec.md
            impl-plan.md
            research.md
            data-model.md
            contracts/
            quickstart.md
            checklists/
              requirements.md
          F-USER-002/
            spec.md
            impl-plan.md
            research.md
            data-model.md
            contracts/
            quickstart.md
            checklists/
              requirements.md

    billing-service/
      EPIC-BILL-001-invoice/
        exec-plan.md
        design/
          index.md
        features/
          ... (将来の F-BILL-*** 機能)
```

**重要な規約:**

* **ExecPlan**: エピックごとに1つ、常に以下の場所に配置されます：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/exec-plan.md
  ```

* **Epic design index (エピック設計インデックス)**: 各エピックごとに 0〜1 個、存在すると望ましい軽量インデックスです：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/design/index.md
  ```

  役割:

  * そのエピックに属する **複数フィーチャ間の関係** や **共有コンテキスト** を、薄いドキュメントとしてまとめる。
  * 各フィーチャの `spec.md` や `impl-plan.md` / `data-model.md` / `contracts/` への **リンク集（目次）** として振る舞う。
  * 「どのエンティティ・API をどのフィーチャが責任を持つか」「どの順序でフィーチャが連携するか」といった情報を一覧できる。

  **システムレベルエピック (`plans/system/...`) では**:

  * `exec-plan.md` と `design/index.md` のみを持つのが基本です。
  * 実際の実装に紐づくフィーチャ（spec/impl-plan/...）は、必ず `plans/services/...` 配下のエピックで管理します。

* **Feature spec (機能仕様書)**: 機能ごとに1つ、常に以下の場所に配置されます：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/spec.md
  ```

  （この `<scope>` は通常 `services` であり、`system` 配下に features/ を作ることは基本的に行いません。）

* **Feature implementation plan (実装計画)**: 機能ごとに 0〜1 個、`/speckit.plan` フローから生成されることを想定します：

  ```text
  plans/<scope>/<service-or-system>/<EPIC-ID>/features/<FEATURE-ID>/impl-plan.md
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
  scripts/validate_spec.sh          # 仕様品質チェックリスト・バリデータ
  scripts/bash/setup-plan.sh        # フィーチャ単位の impl-plan セットアップ
  scripts/powershell/setup-plan.ps1 # 同上（Windows 環境向け）
  ```

* `docs/` — 人間およびエージェント向けのオンボーディング、運用情報、決定事項インデックス。
  この `docs/onboarding.md` は、その中でも「最初に読むべきガイド」です。

---

## 2. コアコンセプト（エピックと機能）

### 2.1 エピック (EPIC-***)

* **大きな作業単位**です（例：「ユーザーオンボーディングフロー」「システム基盤整備」など）。

* 正確に1つの ExecPlan を持ちます：

  ```text
  plans/.../<EPIC-ID>/exec-plan.md
  ```

* `features/` 配下に複数の **機能 (features)** を持つことができます（サービスレベルのエピックの場合）。

* エピックには任意で **軽量な設計インデックス (`design/index.md`)** を持たせることができます。
  これは以下をまとめる場所です：

  * エピック内の全フィーチャの一覧とリンク
  * 共有エンティティ／API／イベント
  * フィーチャ間の依存関係や実行順序
  * 「このエピックのどのあたりに何があるか」を示す地図

**スコープによる違い:**

* `plans/system/...`（システムレベルのエピック）:

  * 原則として **features/ を持ちません**。
  * システム全体の方針・アーキテクチャ・サービス間の境界などを扱い、
    実装に直結する feature は `plans/services/...` 配下のエピックにぶら下がります。
* `plans/services/...`（サービスレベルのエピック）:

  * `features/` 配下に実際の feature（spec/impl-plan/...）を持ちます。
  * API・UI・ドメインロジックといった実装に最も近いレイヤです。

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

* **ひとつのまとまった動作や、ユーザーにとって意味のある小さな価値**を提供する単位です（例：「サインアップページの基本 UI」「メール認証 API」など、利用者が実際に体験できる機能のひと切れ）。
* 独自の **機能仕様書 (feature spec)** と **品質チェックリスト** を持ちます。
* `/speckit.plan` フローを通じて、必要に応じて **機能ごとの実装計画 (impl-plan.md) と設計成果物（research/data-model/contracts/quickstart）** が生成されます。
* `epic_id` を介してエピックにリンクされます。

> 原則として、feature は **services スコープのエピック (`plans/services/...`)** に属します。
> system スコープのエピック (`plans/system/...`) に features/ を直接ぶら下げることは、特別な事情がない限り行いません。

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

* 仕様書は機能単位 (per-feature)、ExecPlan はエピック単位 (per-epic)、
  **エピック設計インデックスは「複数フィーチャをまたぐ設計の目次」** という役割分担です。

---

## 3. ExecPlan と PLANS.md

### 3.1 ExecPlan とは？

**ExecPlan** は、初心者がゼロからエピックを実装する方法を正確に伝える、文章主体の自己完結型ドキュメントです。

* 各エピックディレクトリ直下の `exec-plan.md` に存在します。
* `PLANS.md` のルールに正確に従う必要があります。
* **生きたドキュメント**です：進捗があったり、決定が下されたり、予期せぬ事態が見つかるたびに更新されます。

ExecPlan は、**feature 単位の spec / impl-plan / 設計成果物** と、
**epic 単位の設計インデックス (`design/index.md`)** を束ねる「物語の中心」です。

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

さらに、**`Artifacts and Notes`** には、可能であれば次も含めます：

* `design/index.md` の存在と、その中で管理している共有コンテキスト（例：共通エンティティ、共通 API）。
  例：

  ```markdown
  ### Artifacts and Notes

  - Epic design index: `plans/services/user-service/EPIC-USER-001-onboarding/design/index.md`
    - Shared entities and ownership
    - Shared APIs and contracts
    - Cross-feature flows
  ```

* 各フィーチャの `impl-plan.md` / `data-model.md` / `contracts/` / `quickstart.md` へのリンクまとめ。
  例：

  ```markdown
  - Feature artifacts:
    - F-USER-001:
      - Spec: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md`
      - Impl plan: `.../impl-plan.md`
      - Data model: `.../data-model.md`
      - Contracts: `.../contracts/`
      - Quickstart: `.../quickstart.md`
  ```

これにより、エピックレベルの計画から機能レベルの仕様書や設計成果物への明確なリンクが作成されます。

### 3.3 AIコーディングエージェントによる ExecPlan の使用方法

エピックが割り当てられた場合：

1. `docs/onboarding.md`（このファイル）を読む。

2. `PLANS.md` を完全に読む。

3. `harness/feature_list.json` で定義されているエピックの `exec-plan.md` を開く。

4. ExecPlan 全体を上から下まで読む。

5. もし存在すれば、同じディレクトリ配下の `design/index.md` を開き、
   エピック内のフィーチャ間の関係や共有エンティティ／API をざっくり把握する。

6. `Plan of Work` (作業計画) と `Concrete Steps` (具体的なステップ) に従い、以下を更新する：

   * `Progress`
   * `Surprises & Discoveries`
   * `Decision Log`
   * `Outcomes & Retrospective`

7. ExecPlan は常に **自己完結的** かつ、現在の作業状態に合わせて最新に保つこと。
   エピック内の新しいフィーチャが増えたら、`Related Features / Specs` と `design/index.md` の両方を更新します。

### 3.4 Epic design index (`design/index.md`) のサンプルテンプレート

各エピックの `design/index.md` は、「薄いけれど全体を見渡せる地図」として設計します。
以下は推奨テンプレートです（system / services どちらのエピックでも利用可能です）：

```markdown
# Epic Design Index: [EPIC-ID] [Epic title]

## 1. Scope & Owner

- ExecPlan: `plans/<scope>/<service-or-system>/<EPIC-ID>/exec-plan.md`
- Scope:
  - System or service: [system / service:<service-name>]
  - Primary services: [api-gateway, user-service, ...]
- Summary:
  - [One or two sentences describing the epic’s overall goal and boundaries.]

---

## 2. Feature Map

> この表は「このエピックのどこに何があるか」を一覧するためのものです。

| Feature ID | Title                                | Spec Path                                                     | Impl Plan                         | Data Model                        | Contracts Dir                     | Quickstart                        |
|-----------|--------------------------------------|---------------------------------------------------------------|-----------------------------------|-----------------------------------|-----------------------------------|-----------------------------------|
| F-USER-001 | Signup page basic UI                | `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/spec.md` | `.../impl-plan.md` | `.../data-model.md` | `.../contracts/` | `.../quickstart.md` |
| F-USER-002 | Email verification flow             | `...`                                                         | `...`                             | `...`                             | `...`                             | `...`                             |

（system エピックの場合は、ここに **直接 feature を列挙せず**、  
関連する service エピックや feature へのリンクを載せても構いません）

---

## 3. Shared Entities & Ownership

> 「このエピック全体で使われる重要なエンティティ」と「どの feature が責任を持つか」を整理します。

| Entity        | Owning Feature ID | Services involved              | Notes                                           |
|---------------|-------------------|--------------------------------|-------------------------------------------------|
| User          | F-USER-001        | user-service, api-gateway      | Core user record, used across onboarding flows. |
| VerificationToken | F-USER-002   | user-service                   | Tied to email verification only.                |

---

## 4. Shared APIs / Contracts

> このエピック内で重要な API / メッセージ / イベントと、その所有者をまとめます。

| Contract / Endpoint                  | Owner Feature | Path / Topic                          | Consumers                   | Notes                               |
|--------------------------------------|--------------|---------------------------------------|-----------------------------|-------------------------------------|
| `POST /signup`                       | F-USER-001   | api-gateway → user-service            | Web frontend                | Creates a new pending user.         |
| `POST /verify-email`                | F-USER-002   | api-gateway → user-service            | Web frontend, mobile client | Finalizes user activation.          |

---

## 5. Cross-Feature Flows

> 複数の feature をまたぐ代表的なユーザーフローやバックグラウンドフローを簡潔に記述します。

### Flow: User signup & email verification

1. [F-USER-001] User submits signup form via `/signup`.
2. [F-USER-001] System creates a pending user and sends verification email.
3. [F-USER-002] User clicks the verification link.
4. [F-USER-002] System validates token, activates user, and logs audit event.

---

## 6. Design Decisions (Summary)

> 詳細な履歴は ExecPlan の `Decision Log` に記録し、ここでは「このエピックの設計を理解する上で重要な決定のみ」を短くまとめます。

- Decision: [短いタイトル]
  - Summary: [1–2 文で要約]
  - See: `exec-plan.md` → Decision Log → [ID or date]

---

## 7. Open Questions / TODOs

> 複数の feature にまたがる懸念・未解決事項のみを載せます。

- [ ] [Question or TODO 1]
- [ ] [Question or TODO 2]
```

このテンプレートは「薄く・リンク中心」に保つことが重要です。
詳細な仕様や設計は各 feature の `spec.md` / `impl-plan.md` / `data-model.md` / `contracts/` に記述し、
`design/index.md` はあくまでも「目次」と「共有コンテキストのまとめ」に留めます。

---

## 4. 機能仕様書 (Feature Specs) と `/speckit` フロー

機能仕様書は、**2段階のフロー**で作成および改善されます：

1. `/speckit.specify` — 機能仕様書の作成/更新（spec + checklist の生成）。
2. `/speckit.clarify` — 曖昧さの解消と欠落している決定事項の記入（spec を書き換え）。

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
  → 後段の `/speckit.clarify` がここを優先的に解消します。

チェックリスト (`requirements.md`) は **空のチェックボックスのまま**生成されます。
実際にチェックを埋め、品質ゲートを通すのは Clarify / 手動レビュー / `scripts/validate_spec.sh` の役割です。

### 4.2 `/speckit.clarify` (要件の明確化、人間主導)

Clarify は **要件初期化エージェント**として、次の2種類の曖昧さを解消します：

1. `/speckit.specify` が埋め込んだ **`[NEEDS CLARIFICATION: ...]` マーカー**。
2. Taxonomy ベースのスキャンで見つかる、仕様書の「穴」（機能・データ・UX・非機能・外部連携・エッジケースなど）。

明確化作業は**人間によって手動で実行**されます（完全自動ではありません）：

1. 対象の機能の `spec.md` を開き、ざっと内容を把握します。
   `[NEEDS CLARIFICATION: ...]` マーカーがどこにあるかも確認します。

2. その機能に対して `/speckit.clarify` を実行します。Clarify の内部では：

   * `scripts/*/check-prerequisites.*` を通じて `FEATURE_SPEC` / `FEATURE_DIR` が特定されます。

   * `spec.md` を読み込み、

     * 明示的な `[NEEDS CLARIFICATION]` マーカー、
     * taxonomy（機能、データモデル、UX、非機能、外部連携、エッジケース、制約など）
       をもとに曖昧さの「候補リスト」を作ります。

   * その中から **最大 5 個** の高インパクトな質問をキューに積みます：

     * 優先度は `[NEEDS CLARIFICATION]` マーカー ＞ 高インパクトな taxonomy の穴。

3. Clarify は質問を **1つずつ** 提示します：

   1. まず、その質問が

      * **どの曖昧さ／どんな決定を解消しようとしているのか**
      * それが **なぜ重要か**（スコープやセキュリティ、UX、データモデル、運用リスクなどにどう効くか）

      を 1〜2 行で説明します。
      → 「この質問に答えると何がスッキリするのか」が先に分かるようにします。

   2. 次に、その問いに対する **候補となる解決策を 5〜7 個** 洗い出し、それぞれに対して：

      * 短いラベル（Answer）
      * 推奨度（⭐1〜⭐5 の 5 段階）
      * 簡単な理由（なぜその評価なのか）

      を付けます。

      * ⭐⭐⭐⭐⭐ … 強く推奨（このプロジェクトでは最有力）
      * ⭐⭐⭐⭐ … 推奨（とても良いが、いくつかトレードオフあり）
      * ⭐⭐⭐ … 妥当だが明確なトレードオフあり
      * ⭐⭐ … あまり推奨しない（特定の事情があるときのみ）
      * ⭐ … 原則として避けたい

      この 5〜7 個の候補の中から、**2〜4 個の「有力候補」**（多くは ⭐⭐⭐⭐ 以上）を特定し、そのうち 1 つを **最有力の推奨案** として扱います。

      表示形式のイメージ：

      ```markdown
      **Recommended:** Option B (⭐⭐⭐⭐⭐) - <なぜこれが一番良さそうかを 1〜2 文で>

      | Option | Answer                                   | Recommendation | Rationale                                  |
      |--------|------------------------------------------|----------------|--------------------------------------------|
      | A      | <Option A description>                  | ⭐⭐⭐⭐          | <なぜ強い候補か>                           |
      | B      | <Option B description>                  | ⭐⭐⭐⭐⭐         | <なぜ最有力か>                             |
      | C      | <Option C description>                  | ⭐⭐⭐           | <どんなトレードオフがあるか>               |
      | D      | <Option D description>                  | ⭐⭐            | <なぜ弱い選択肢か>                         |
      | E      | <Option E description>                  | ⭐             | <なぜ基本的に避けたいか>                   |
      | Short  | Provide a different short answer (<=5 words) | —        | 上記にない独自案を短く指定したい場合用     |
      ```

      * `Short` 行は「5語以内の自由記述」を受け付けるための枠です。
      * 全体として、**候補数（A〜E + Short を含めて 5〜7 個）** に収まるようにします。

   3. 人間（プロダクトオーナー／テックリードなど）は、次のいずれかの形で回答します：

      * 最有力案を採用する場合：

        * `"yes"` または `"recommended"` と返す
          → テーブルの中で **Recommended:** と明示された Option（例：B）を採用したものとして扱います。
      * 別の候補を選ぶ場合：

        * `"A"`, `"B"`, `"C"` … といった **Option のアルファベット**を返す
          → 対応する行の Answer を採用します。
      * 独自案を指定する場合：

        * 5語以内の短いテキストで回答します（例： `"Email only"`, `"Admin only"`, など）
          → テーブルの `Short` 行を選んだものとして扱い、その内容を最終回答とします。

      回答が曖昧な場合（複数候補にまたがる、意味が取りづらいなど）は、Clarify 側が**同じ質問の中で**短く確認を行います（この確認は「別の質問」としてカウントしません）。

4. 人間の回答を受け取るたびに Clarify は：

   * 関連する `[NEEDS CLARIFICATION: ...]` マーカーがあれば、それを削除し、周囲の文章を **自然な形に書き換え** ます。
   * taxonomy 起点の質問であれば、該当セクション（Functional Requirements / Data Model / Success Criteria など）を直接更新します。
   * **`## Clarifications` セクションは作りません**。
     仕様書は「最初から正しく書かれていた」ように読める状態にします。

5. Clarify は 1 セッションあたり最大 5 問まで質問し、
   質問ごとに spec を保存していきます（atomic overwrite を想定）。

6. セッション終了時、Clarify は：

   * このセッションで解消した質問数（/NEEDS CLARIFICATION マーカー数）。
   * どのセクションを更新したか（Functional Requirements / Data Model / Success Criteria など）。
   * まだ残っている `[NEEDS CLARIFICATION]`（あれば）。
   * taxonomy ベースのカバレッジ（Resolved / Deferred / Clear / Outstanding）
     をまとめて報告し、
   * 次のステップとして `/speckit.plan` へ進んでよいか、あるいはもう一度 Clarify / 手動修正を挟むべきかを提案します。

> Clarify はあくまで「仕様書の穴を減らすための前処理」です。
> 最終的な品質ゲートは `scripts/validate_spec.sh` とチェックリストの完了で担保します。

---

## 5. 仕様品質ゲート (`scripts/validate_spec.sh`)

機能が「計画 / 実装の準備完了」と見なされる前に、**仕様品質チェックリスト (Specification Quality Checklist)** に合格する必要があります。

### 5.1 チェックリストの場所

各機能に対して：

```text
plans/.../<EPIC-ID>/features/<FEATURE-ID>/checklists/requirements.md
```

このファイルは `/speckit.specify` によって作成され、Clarify / 手動編集 / レビューを通じて 1 つずつチェックが埋められていきます。

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

3. `/speckit.clarify` を実行し：

   * `[NEEDS CLARIFICATION]` マーカーが解消されていくこと、
   * taxonomy ベースの高インパクトな穴（非機能やエッジケースなど）が埋められていくこと
     を確認する。

4. 機能のチェックリストがパスするまで `scripts/validate_spec.sh` を実行する。

5. エピックの `exec-plan.md` の `Related Features / Specs (関連フィーチャ ID 一覧)` にこの機能がリストされていることを確認する。

6. 必要に応じて、そのエピック配下の `design/index.md` にも追記する：

   * 新しいフィーチャ ID とタイトル
   * 主に扱うエンティティ・API
   * 既存フィーチャとの依存関係があれば簡単な説明

### 6.2 AIコーディングエージェント向け (実装作業)

エピックが割り当てられた場合：

1. `docs/onboarding.md`（このファイル）を読む。

2. `PLANS.md` を完全に読む。

3. `harness/feature_list.json` を読み込み、以下を行う：

   * ターゲットとなるエピック (`epic_id`, `exec_plan_path`)。
   * 関連する機能 (`spec_path`, `checklist_path`)。

4. 各関連機能について：

   * `spec.md` が存在するか、
   * 必要に応じて Clarify が済んでいるか（曖昧さが許容範囲か）、
   * `scripts/validate_spec.sh` が PASS しているか
     → **impl-plan を生成する前提条件** になります。

5. エピックの `exec-plan.md` を開く。

6. もし存在すれば、同じエピック配下の `design/index.md` を開き、
   フィーチャ間の関係と共有コンテキストを把握する。

7. 個々のフィーチャに対して `/speckit.plan` を実行し、`impl-plan.md` および関連設計成果物（research/data-model/contracts/quickstart）を生成・更新する。

8. エピックの `exec-plan.md` に従って実装する：

   * 停止するポイントごとに `Progress` を更新する。
   * 自明でない設計上の選択は `Decision Log` に記録する。
   * 予期しない動作は `Surprises & Discoveries` に記録する。
   * `Validation and Acceptance` の記述に従ってテストを追加・実行する。
   * 複数フィーチャにまたがる設計変更があれば `design/index.md` を更新する。

9. すべてを **安全、冪等、かつ再現可能** に保つ。

---

## 7. クイックチェックリスト (新しいセッションを開始するエージェント向け)

1. ✅ `docs/onboarding.md`（このファイル）を読む。
2. ✅ `PLANS.md` を読む。
3. ✅ `harness/feature_list.json` を検査して以下を特定する：
   * ターゲットとなるエピック (`epic_id`, `exec_plan_path`)。
   * 関連する機能 (`spec_path`, `checklist_path`)。
4. ✅ 関連する機能仕様書が存在し、必要に応じて `/speckit.clarify` が実行されていることを確認する。
5. ✅ `scripts/validate_spec.sh` を使って該当機能のチェックリストがパスすることを確認する（計画・実装の前提）。
6. ✅ エピックの `exec-plan.md` を開き、すべてのセクションを更新しながらそれに従う。
7. ✅ エピック配下に `design/index.md` があれば内容を確認し、
   変更に伴い必要なら更新する（無ければ、クロスフィーチャな設計が出てきたタイミングで作成を検討する）。

これらの前提条件のいずれかが欠けている場合、**パスや構造を推測しないでください**。
その代わり、欠落している成果物を `harness/AI-Agent-progress.txt` または ExecPlan の `Progress` / `Surprises & Discoveries` に記録し、人間の入力を待つために停止してください。