# 長期稼働型 AI エージェント

このリポジトリは、**長期稼働するAIコーディングエージェントと人間が協働するため**に設計されたテンプレートです。

主要な概念は以下の通りです：
- 自明な作業以外のすべての作業は、**機能仕様書 (Feature Spec)** と **実行計画 (ExecPlan)** によって主導されます。わざわざ計画書を作るまでもない小規模な作業では作成しません。
- 仕様書 (Specs) は **機能単位 (per-feature)** です（小さな単位）。
- 実行計画 (ExecPlans) は **エピック単位 (per-epic)** です（より大きな作業単位）。
- 重要なことはすべてファイルに書き込まれるため、ステートレスなエージェントであっても常に途中から再開できます。

## コンセプト

- 人間エンジニアの習慣を“外部成果物”として強制する。
- 「ハーネス」というのは、エージェントの振る舞いを決める外側の仕組みのこと。
- Anthropic は、人間のエンジニアがふだん行っていること（タスク分解、チケット管理、コミットログ、テスト、進捗メモなど）を、「ファイルやスクリプトという形の成果物として必ず残させる」ようにした。このやり方をエージェントも真似できるようにした。

## 用語と関係性

- AI-Agent-progress.txt: 「時間軸のログ」（セッション横断で何がいつ起きたか）
  - いつ何が起きたかの高レベルな履歴 → AI-Agent-progress.txt を時系列に追えば分かる。ExecPlan の Progress 更新履歴など。
- ExecPlan: 「エピック単位の設計＋作業計画＋進捗＋決定」（そのエピックに閉じたストーリー）
  - 細かいストーリーと背景 → ExecPlan を読めば分かる。
- architecture/: 「システム全体の設計図」（静的なアーキテクチャの説明）
  - 「いま・あるいは目指すべきシステム構造」を、実装から少し距離をおいて説明する層。
- plans/system/: 「システム全体エピック用の ExecPlan」（アーキテクチャを“実現・変更するための計画書」）
  - architecture に書かれた方向性・設計を、実際のコードベースに落とし込むためのステップバイステップの計画。

| 視点  | AI-Agent-progress.txt                     | ExecPlan (`exec-plan.md`)            |
| --- | ----------------------------------------- | ------------------------------------ |
| 単位  | リポジトリ全体・全エピック横断                           | **1 エピックごと**（`EPIC-XXX-YYY` 単位）      |
| 中身  | 時系列のイベントログ（いつ・何が行われたかの一行メモ）               | 目的・文脈・作業計画・進捗・決定・振り返りを含む**長文ドキュメント** |
| 時間軸 | セッション横断・全期間                               | そのエピックのライフサイクル                       |
| 粒度  | 「○○を実行した」「spec check FAILED」など比較的ざくっとした記録 | どのファイルをどう編集し、どんなコマンドをどう実行するかまで詳細     |
| 使い道 | ハーネス視点の監査ログ・CI やエージェントの挙動トレース             | 実装者／エージェントが**このエピックを完遂するために読む“手順書”** |

```text
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

## 全体チェーン

ExecPlan → design/index.md → 各 feature の impl-plan → tasks.md

- /speckit.plan … フィーチャごとの impl-plan と設計 artifacts を作る
- /speckit.tasks … その impl-plan ＋設計 artifacts から「実行タスク」を起こす

## 品質ゲート

- Spec Kit は「specify → clarify → (仕様品質ゲート: scripts/validate_spec.sh) → Plan → (Plan品質ゲート: scripts/validate_plan.sh) → Tasks  → (Task品質ゲート) → Implement → (実装ゲート: コード&セキュリティレビュー)」のゲート制で回すので、1つのプロンプトに詰め込みすぎないこと
- /plan は Plan を作るだけ。タスク分解は /speckit.tasks、実装は /speckit.implement に流すのが基本ラインです。
- /speckit.plan で生成されるものは以下。以下をPlan品質ゲートでチェックする
  - impl-plan.md
  - research.md
  - data-model.md
  - contracts/
  - quickstart.md

- Plan品質ゲートのステップ
  - AIエージェントのレビューで 各フィーチャの `checklists/PlanQualityGate.md` を埋める。/plan コマンド実行で自動的に PlanQualityGate.md が作成される。

## Onboarding

このリポジトリで具体的な作業を始めるときは、詳細な手順やディレクトリ構成、`/speckit.*` フローや `scripts/validate_spec.sh` の使い方をまとめた
* `docs/onboarding.md`
を最初に参照してください。

以降のセッションでは、README を毎回読み直す必要はなく、`docs/onboarding.md` と各 ExecPlan / spec を見れば十分です。