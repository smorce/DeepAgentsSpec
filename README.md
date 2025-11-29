# 追加で作らないといけないプロンプトは何か？

【done】## 1. ExecPlan の一段前に「機能仕様レイヤ」を導入する
・その spec を前提に、コーディングエージェントが ExecPlan（EPIC-XXX-YYY.md） を作る
→ここだけ指示するプロンプトを作る。ExecPlan の一段前の作業工程として追加。
「spec を参照して ExecPlan を生成してください。」
→ 「PLANS.md の修正」と「specify.md の修正」で /speckit.specify が使えるようになった。ディレクトリ構造も決めた。

【done】## 3. Specification Quality Checklist を Harness の品質ゲートに昇格
・FEATURE_DIR/checklists/requirements.md
→これは /speckit.specify コマンド実行で、自動的に生成されるが、保証がないのでより確実性を高めるという意味。
→ scripts/validate_spec.sh を作成した。

【done】## 4. Clarify エージェントを「要件初期化エージェント」として採用
・これはREADMEの手順書として残しておく。
→「/speckit.specify  →  /speckit.clarify  の手順で実行してください」
ただ、 clarify の提案が、前提条件を書いてもらわないと何の話なのか分からない。
推奨度付き選択肢くんの方が分かりやすいので、少し clarify のプロンプトを調整した方が良いかも。
→ plans/README.md に書いた




## 方針
結論から言うと、この speckit の性質と「長期間動くエージェント＋ブランチ運用」を考えると、仕様書 spec はフィーチャ単位で作るほうがエージェントはかなり扱いやすいです。
ただし「エピック単位の視点」は ExecPlan 側でちゃんと持つ、という役割分担にするとバランスが良いです。
/speckit.specify は「1 回のコマンド＝1 個の機能説明＝1 個のブランチ」という動きなので、
1 ブランチ ↔ 1 フィーチャ ↔ 1 spec.md ↔ 1 checklist
という対応にすると、エージェント側のメンタルモデルがシンプルになる。
長期間動くエージェントにとっては：
- 小さめの spec（1 フィーチャ分）だと、「毎回少しだけ進めて成果物を残す」単位が明確
- ブランチと spec が 1 対 1 なので、「今どの spec を編集すべきか」で迷わない
一方、エピック全体の見取り図や優先順位は、ExecPlan 側の Progress / Plan of Work / Context and Orientation でまとめて持てばよいので、
「エピックの視点」は ExecPlan に寄せ、仕様の細かさはフィーチャ側に寄せるという分担がきれいにハマる。

### メリット
speckit 側：
- 「どのフィーチャの spec / checklist を編集すべきか」を
- features[].spec_path / features[].checklist_path から機械的に決定可能。

ExecPlan 側：
- epics[].exec_plan_path だけ見れば「このエピック全体の計画書」に飛べる。
- ExecPlan 内から features の ID（F-XXX-YYY）を列挙して参照できる。

エージェント：
- 「今 F-USER-001 をやっている」＝
  - 見る spec: features[F-USER-001].spec_path
  - 直す checklist: features[F-USER-001].checklist_path
  - 所属するエピックの計画: epics[epic_id].exec_plan_path
というシンプルな 3 つの参照で済む。


## done
- PLANS.md の修正
- specify.md の修正(これでコマンドが使えるようになった)



# 長期間実行されるエージェントのための効果的なハーネス

## 概要
ポイントは「最初の一回だけ動く初期化エージェント」と「毎回少しずつ進めて、必ず成果物（コード、ExecPlan、ログなど）を残すコーディングエージェント」の役割分担です。個々のエピックに対する ExecPlan（実行計画書）を作成し、管理するのもコーディングエージェントです。

解決の方向性：人間エンジニアの習慣を“外部成果物”として強制する
- 「ハーネス」というのは、エージェントの振る舞いを決める外側の仕組みのことです。
- Anthropic は、人間のエンジニアがふだん行っていること（タスク分解、チケット管理、コミットログ、テスト、進捗メモなど）を、「ファイルやスクリプトという形の成果物として必ず残させる」ようにしました。

## PLANS.md
PLANS.md とは、AIエージェントが長時間・複雑なタスクを実行するために使われる「実行計画（ExecPlan）」のテンプレート文書です。
PLANS.md は実装する機能や変更内容を、初心者でも理解できるように「全体像」「目的」「作業手順」「バリデーション方法」などを詳細に書き出すことを目的としています。

最初にユーザーがAIエージェントに、実装したい機能や目的、必要な条件を提示すると、AIエージェントがその要件に基づき、PLANS.md を使って実行計画（ExecPlan）を作成します。

## ExecPlan（エピックごとの実行計画）
- タイトル：短く、行動志向の説明。
- Purpose / Big Picture (目的 / 全体像)：ユーザーがこの変更から何を得るか、動作を確認する方法を説明。
- Progress (進捗)：チェックボックス付きリストが必須。停止するたびに完了/残存タスクを記録し、タイムスタンプが推奨される。
- Surprises & Discoveries (驚きと発見)：実装中に発見された予期せぬ挙動、バグ、洞察を短い証拠スニペットとともに文書化。
- Decision Log (決定ログ)：重要な設計上の決定とその理由を記録。
- Outcomes & Retrospective (成果と振り返り)：主要なマイルストーンまたは完了時に、達成されたこと、課題、教訓を要約。
- Context and Orientation (文脈とオリエンテーション)：読者が何も知らないと仮定して、現在の状態を説明。キーファイルをフルパスで指定。
- Plan of Work (作業計画)：編集と追加の順序を散文で具体的に記述。
- Concrete Steps (具体的なステップ)：実行する正確なコマンドと作業ディレクトリを明記し、予想される出力も示す。
- Validation and Acceptance (検証と受け入れ)：検証はオプションではない。システム起動方法、観察すべき動作を、人が検証できる行動として記述する。

## ディレクトリ構造
ドメインの切り口ではなくサービス単位の切り口で、全体アーキテクチャ → マイクロサービス の構造。
- 物理構造：全体アーキテクチャ → 各マイクロサービス
- 論理構造：共通の feature_list.json ＋ エピックごとの ExecPlan
- 設計履歴：ExecPlan の Decision Log を一次情報、docs/decisions.md を索引
「spec はフィーチャ単位」＋「ExecPlan はエピック単位」
```
project-root/                               # リポジトリのルート
├── PLANS.md                                # ExecPlan の規約ドキュメント（Codex Execution Plans）
│
├── README.md
├── architecture/                           # 「全体アーキテクチャ」レイヤ
│   ├── system-architecture.md              # 全体構成図・コンポーネント図の説明
│   ├── service-boundaries.md               # 各マイクロサービスの責務・境界・インタフェースの定義
│   ├── deployment-topology.md              # デプロイ構成（K8s/VM/サーバレスなど）の概要
│   └── diagrams/                           # 図（PlantUML, mermaid, 画像ファイルなど）
│
├── harness/                                # 長期間実行エージェント用ハーネス（横断的なメタ情報）
│   ├── init.sh                             # リポジトリ全体の初期化・テスト起動スクリプト
│   ├── AI-Agent-progress.txt               # セッション横断の進捗ログ（人間可読）
│   ├── feature_list.json                   # エピック／フィーチャのマスタ + spec/ExecPlan パスの対応表
│   └── harness-config.yaml                 # ハーネスの設定（サービス一覧・スクリプトパスなど）
│
├── plans/                                  # エピック単位の「計画・仕様」置き場
│   ├── README.md                           # ExecPlan / spec 運用ルール（PLANS.md へのポインタなど）
│   │
│   ├── system/                             # システム全体にまたがるエピック用
│   │   └── EPIC-SYS-001-foundation/        # 例: 基盤整備エピックのディレクトリ（EPIC ごとに 1 フォルダ）
│   │       ├── exec-plan.md                # エピック全体の ExecPlan（PLANS.md 準拠の実行計画）
│   │       │                               #   → タスク分解・進捗・Decision Log などはここで管理
│   │       └── features/                   # このエピック配下の「フィーチャ仕様」をまとめる
│   │           └── F-SYS-001/              # 例: "Repository scaffold initialized" フィーチャ
│   │               ├── spec.md             # フィーチャ単位の仕様書（/speckit.specify の出力先）
│   │               └── checklists/         # フィーチャ仕様の品質ゲート用チェックリスト
│   │                   └── requirements.md # Specification Quality Checklist
│   │
│   └── services/                           # 各マイクロサービス別のエピック用
│       ├── api-gateway/                    # api-gateway サービスに関するエピック群
│       │   └── EPIC-API-001-routing/       # 例: ルーティング周りのエピックディレクトリ
│       │       ├── exec-plan.md            # このエピック全体の ExecPlan
│       │       └── features/               # このエピックに属するフィーチャ仕様を集約
│       │           └── F-API-001/          # 例: "Basic health check endpoint"
│       │               ├── spec.md         # GET /health の仕様など、ユーザー価値レベルで記述
│       │               └── checklists/
│       │                   └── requirements.md
│       │
│       ├── user-service/                   # user-service に関するエピック群
│       │   └── EPIC-USER-001-onboarding/   # 例: ユーザーオンボーディングのエピックディレクトリ
│       │       ├── exec-plan.md            # オンボーディング全体の ExecPlan（複数フィーチャを束ねる）
│       │       └── features/
│       │           ├── F-USER-001/         # "Signup page basic UI"
│       │           │   ├── spec.md         # /signup 画面 UI の仕様
│       │           │   └── checklists/
│       │           │       └── requirements.md
│       │           └── F-USER-002/         # "Signup API endpoint"
│       │               ├── spec.md         # POST /api/users の仕様
│       │               └── checklists/
│       │                   └── requirements.md
│       │
│       └── billing-service/                # billing-service に関するエピック群
│           └── EPIC-BILL-001-invoice/      # 例: 請求書発行のエピックディレクトリ
│               ├── exec-plan.md            # 請求書発行エピックの ExecPlan
│               └── features/               # （将来追加されるフィーチャの仕様書置き場）
│                   └── ...                 # F-BILL-001 などを同様に追加
│
├── services/                               # 各マイクロサービスの実装
│   ├── api-gateway/
│   │   ├── README.md                       # このサービス固有の説明・起動方法など
│   │   ├── service-architecture.md         # このサービス内部の構成・依存関係
│   │   ├── src/                            # サービス本体のソースコード
│   │   ├── tests/
│   │   │   ├── unit/                       # ユニットテスト
│   │   │   └── integration/                # サービス単体の結合テスト
│   │   ├── scripts/
│   │   │   ├── run_unit_tests.sh
│   │   │   └── run_integration_tests.sh
│   │   ├── Dockerfile
│   │   └── service-config.example.yaml
│   │
│   ├── user-service/
│   │   ├── README.md
│   │   ├── service-architecture.md
│   │   ├── src/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── scripts/
│   │   ├── Dockerfile
│   │   └── service-config.example.yaml
│   │
│   └── billing-service/
│       ├── README.md
│       ├── service-architecture.md
│       ├── src/
│       ├── tests/
│       │   ├── unit/
│       │   └── integration/
│       ├── scripts/
│       ├── Dockerfile
│       └── service-config.example.yaml
│
├── tests/                                  # システム全体視点のテスト
│   └── e2e/
│       ├── scenarios/                      # ユーザストーリー単位の E2E シナリオ
│       ├── helpers/                        # E2E で使う共通ヘルパー・ユーティリティ
│       └── puppeteer.config.js
│
├── scripts/                                # リポジトリ横断で使う共通スクリプト
│   ├── run_all_unit_tests.sh
│   ├── run_all_e2e_tests.sh
│   └── format_or_lint.sh
│
├── templates/                              # 生成プロンプトやひな型
│   └── commands/
│       └── specify.md                      # /speckit.specify
└── docs/                                   # ドキュメント類
    ├── onboarding.md                       # 新規メンバー／エージェント向け導入ガイド
    ├── decisions.md                        # 重要な設計判断の索引（詳細は各 ExecPlan の Decision Log）
    └── operations.md                       # 運用・監視・SRE 向け情報
```




# 長期稼働型 AI エージェント

このリポジトリは、**長期稼働するAIコーディングエージェントと人間が協働するため**に設計されています。

主要な概念は以下の通りです：

- 自明な作業以外のすべての作業は、**機能仕様書 (Feature Spec)** と **実行計画 (ExecPlan)** によって主導されます。わざわざ計画書を作るまでもない小規模な作業では作成しません。
- 仕様書 (Specs) は **機能単位 (per-feature)** です（小さな単位）。
- 実行計画 (ExecPlans) は **エピック単位 (per-epic)** です（より大きな作業単位）。
- 重要なことはすべてファイルに書き込まれるため、ステートレスなエージェントであっても常に途中から再開できます。

## コンセプト

- 人間エンジニアの習慣を“外部成果物”として強制する
- 「ハーネス」というのは、エージェントの振る舞いを決める外側の仕組みのこと。
- Anthropic は、人間のエンジニアがふだん行っていること（タスク分解、チケット管理、コミットログ、テスト、進捗メモなど）を、「ファイルやスクリプトという形の成果物として必ず残させる」ようにした。このやり方をエージェントも真似できるようにした。

## 用語と関係性

- AI-Agent-progress.txt: 「時間軸のログ」（セッション横断で何がいつ起きたか）
  - いつ何が起きたかの高レベルな履歴 → AI-Agent-progress.txt を時系列に追えば分かる。ExecPlan の Progress 更新履歴など。
- ExecPlan: 「エピック単位の設計＋作業計画＋進捗＋決定」（そのエピックに閉じたストーリー）
  - 細かいストーリーと背景 → ExecPlan を読めば分かる
- architecture/: 「システム全体の設計図」（静的なアーキテクチャの説明）
  - 「いま・あるいは目指すべきシステム構造」を、実装から少し距離をおいて説明する層
- plans/system/: 「システム全体エピック用の ExecPlan」（アーキテクチャを“実現・変更するための計画書」）
  - architecture に書かれた方向性・設計を、実際のコードベースに落とし込むためのステップバイステップの計画

| 視点  | AI-Agent-progress.txt                     | ExecPlan (`exec-plan.md`)            |
| --- | ----------------------------------------- | ------------------------------------ |
| 単位  | リポジトリ全体・全エピック横断                           | **1 エピックごと**（`EPIC-XXX-YYY` 単位）      |
| 中身  | 時系列のイベントログ（いつ・何が行われたかの一行メモ）               | 目的・文脈・作業計画・進捗・決定・振り返りを含む**長文ドキュメント** |
| 時間軸 | セッション横断・全期間                               | そのエピックのライフサイクル                       |
| 粒度  | 「○○を実行した」「spec check FAILED」など比較的ざくっとした記録 | どのファイルをどう編集し、どんなコマンドをどう実行するかまで詳細     |
| 使い道 | ハーネス視点の監査ログ・CI やエージェントの挙動トレース             | 実装者／エージェントが**このエピックを完遂するために読む“手順書”** |

```関係性
architecture/
  ├── system-architecture.md
  ├── service-boundaries.md
  ├── deployment-topology.md
  └── diagrams/
       ↑
       │（システムの「あるべき姿」「全体像」を説明）
       │
plans/system/
  └── EPIC-SYS-001-foundation/exec-plan.md
       ↑
       │（architecture を前提に、
       │  「このリポジトリで何をどう変えるか」を落とし込む）
       │
services/, tests/, scripts/
  （ExecPlan に従って、実際のコード・テスト・スクリプトが変更される）
```

---

## 1. 最上位レイアウト（全体構成）

リポジトリルートからの構成：

```text
project-root/
├── PLANS.md                # ExecPlan のルールと骨子（これに必ず従うこと）
├── README.md               # 現在地（このファイル）
│
├── architecture/           # システムレベルのアーキテクチャドキュメント
├── harness/                # 横断的なメタデータとハーネス用スクリプト
├── plans/                  # エピックおよび機能レベルの仕様書
├── services/               # マイクロサービスの実装
├── templates/              # 生成プロンプトやひな型
├── tests/                  # E2Eおよびシステムレベルのテスト
├── scripts/                # リポジトリ全体のヘルパースクリプト
└── docs/                   # オンボーディング、決定事項インデックス、運用情報
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

---

## 2. コアコンセプト

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

1. この `README.md` を読む。
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

* 入力：自然言語による機能説明（`/speckit.specify` の後のテキスト）。何を構築しようとしているのか、そしてなぜ構築しようとしているのかを可能な限り明確に記述してください。この時点では技術スタックに焦点を当てないでください。
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

1. `README.md`（このファイル）を読む。
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

1. ✅ `README.md`（このファイル）を読む。
2. ✅ `PLANS.md` を読む。
3. ✅ `harness/feature_list.json` を検査して以下を特定する：
   * ターゲットとなるエピック (`epic_id`, `exec_plan_path`)。
   * 関連する機能 (`spec_path`, `checklist_path`)。
4. ✅ 関連する機能仕様書が存在し、`scripts/validate_spec.sh` をパスすることを確認する。
5. ✅ エピックの `exec-plan.md` を開き、すべてのセクションを更新しながらそれに従う。

これらの前提条件のいずれかが欠けている場合、**パスや構造を推測しないでください**。
その代わり、欠落している成果物を `harness/AI-Agent-progress.txt` または ExecPlan の `Progress` / `Surprises & Discoveries` に記録し、人間の入力を待つために停止してください。