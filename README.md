# 追加で作らないといけないプロンプトは何か？

【doing】## 1. ExecPlan の一段前に「機能仕様レイヤ」を導入する
・その spec を前提に、コーディングエージェントが ExecPlan（EPIC-XXX-YYY.md） を作る
→ここだけ指示するプロンプトを作る。ExecPlan の一段前の作業工程として追加。
「spec を参照して ExecPlan を生成してください。」

## 3. Specification Quality Checklist を Harness の品質ゲートに昇格
・FEATURE_DIR/checklists/requirements.md
→これは /speckit.specify コマンド実行で、自動的に生成されるが、保証がないのでより確実性を高めるという意味。

## 4. Clarify エージェントを「要件初期化エージェント」として採用
・これはREADMEの手順書として残しておく。
→「/speckit.specify  →  /speckit.clarify  の手順で実行してください」
ただ、 clarify の提案が、前提条件を書いてもらわないと何の話なのか分からない。
推奨度付き選択肢くんの方が分かりやすいので、少し clarify のプロンプトを調整した方が良いかも。

===================
(1)
3. Specification Quality Checklist を Harness の品質ゲートに昇格
を採用します。
scripts/validate_spec.sh を作成してください。これは未チェックボックスが残っていないかをチェックし、harness/AI-Agent-progress.txt に「spec quality check: PASSED/FAILED」「未達項目の箇条書き」をを残させるスクリプトです。

(2)
4. Clarify エージェントを「要件初期化エージェント」として採用
を採用します。
ただし、エージェントではなく人間がステップを手作業で実行します。なので、「/speckit.specify  →  /speckit.clarify  の手順で実行してください」 みたいな内容をREADMEの手順書として残そうと思います。
=====================

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



/speckit.specify の「SPEC_FILE の出力先」を features/F-XXX-YYY/spec.md 前提に書き換える

ExecPlan テンプレート（PLANS.md）に「関連フィーチャ ID 一覧」セクションを追加する




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
├── architecture/                           # 「全体アーキテクチャ」レイヤ
│   ├── system-architecture.md              # 全体構成図・コンポーネント図の説明
│   ├── service-boundaries.md               # 各マイクロサービスの責務とインタフェース
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
└── docs/                                   # ドキュメント類
    ├── onboarding.md                       # 新規メンバー／エージェント向け導入ガイド
    ├── decisions.md                        # 重要な設計判断の索引（詳細は各 ExecPlan の Decision Log）
    └── operations.md                       # 運用・監視・SRE 向け情報
```