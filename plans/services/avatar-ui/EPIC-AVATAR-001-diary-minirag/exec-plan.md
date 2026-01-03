# EPIC-AVATAR-001-DIARY-MINIRAG: 日記会話の構造化とMiniRAG連携

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository stores the ExecPlan guidelines in `./PLANS.md` at the repository root. This document must be maintained in accordance with PLANS.md.

This epic has an epic-level design index at `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`. It contains a feature map, shared entities, API/contract references, and the cross-feature flow summary for this epic. The ExecPlan remains self-contained and repeats the critical context below.

## Purpose / Big Picture

ユーザーは avatar-ui で Gemini と日記会話を行い、会話終了時にボタン操作で会話内容を構造化し、MiniRAG に登録できるようになります。さらに、Gemini は必要時に MiniRAG 検索を自律的に呼び出し、過去日記のコンテキスト（doc_id / summary / body）だけを受け取って会話を継続できます。UI には検索の ON/OFF トグルと top_k 設定が表示され、ユーザーが主導で体験を制御できることが可視化されます。

## Related Features / Specs

- F-AVATAR-001: 日記会話の構造化登録とMiniRAG検索連携
  - Spec: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`
  - Status: implemented

## Progress

- [x] (2026-01-03 09:13Z) Epic の初期 ExecPlan と設計ドキュメント骨子を作成した。
- [x] (2026-01-03 09:20Z) Spec / Impl Plan / Research / Data Model / Contracts / Quickstart を整備し、品質ゲートを PASS にした。
- [x] (2026-01-03 09:20Z) avatar-ui のサービス設計ドキュメントを更新し、計画との差分を解消した。
- [x] (2026-01-03 09:20Z) 実装準備としてタスク分解を完了し、Jules Issue 作成へ移行した。
- [x] (2026-01-03 12:20Z) MiniRAG クライアントと日記確定 API を実装し、UI に検索トグルと会話確定を追加した。
- [x] (2026-01-03 12:20Z) settings.json5 と README を更新し、日記ワークフローと設定項目を反映した。

## Surprises & Discoveries

- Observation:

  Spec と Plan の品質ゲートは新規チェックリストに対して PASSED となった。

  Evidence:

    [2026-01-03 09:20Z] spec quality check: PASSED

    [2026-01-03 09:20Z] plan quality check: PASSED

## Decision Log

- Decision: 会話終了はユーザーのボタン操作で確定し、確定時に Gemini が会話を分析して重要度・サマリー・セマンティック記憶・エピソード記憶を生成する。
  Rationale: 日記用途ではユーザーの「ここまで」を明示できる UX が必要であり、自動終了判定より誤登録を減らせるため。
  Date/Author: 2026-01-03 / codex

- Decision: MiniRAG の検索コンテキストは doc_id / summary / body の上位N件のみを Gemini に渡す。
  Rationale: 回答そのものではなく文脈だけを渡すことで、Gemini が会話を継続しやすく、過剰な情報注入を避けられるため。
  Date/Author: 2026-01-03 / codex

- Decision: workspace は固定値 `diary` とし、UI で変更しない。
  Rationale: 個人日記用途で運用が単純化でき、検索フィルタも明確になるため。
  Date/Author: 2026-01-03 / codex

- Decision: 検索トグルと top_k 設定は server 側でスレッドごとに保持し、UI 初期値は `/agui/config` から配布する。
  Rationale: UI と検索ツールが同じ設定ソースを参照でき、Gemini のツール呼び出しと UX の整合性を保てるため。
  Date/Author: 2026-01-03 / codex

## Outcomes & Retrospective

UI への検索トグル・top_k・会話確定ボタン追加と、FastAPI 側の MiniRAG 連携 API を実装した。search_diary ツール経由で Gemini が過去日記検索を行えるようになり、会話確定の結果が UI に表示される。

## Context and Orientation

このエピックは avatar-ui のみを変更対象とし、MiniRAG API は既存の api-gateway 側を利用する前提です。avatar-ui にはフロントエンド（`services/avatar-ui/app/`）と FastAPI ベースの AG-UI サーバー（`services/avatar-ui/server/`）があり、UI は `/agui` に接続して Gemini との会話を行います。本機能では UI に「検索トグル」「top_k 設定」「会話確定ボタン」を追加し、サーバー側に MiniRAG 呼び出しと会話構造化のフローを追加します。

重要なファイルは次のとおりです。

- UI: `services/avatar-ui/app/src/renderer/index.html`, `services/avatar-ui/app/src/renderer/main.ts`, `services/avatar-ui/app/src/renderer/style.css`
- サーバー: `services/avatar-ui/server/main.py`, `services/avatar-ui/server/src/config.py`
- 設定: `services/avatar-ui/settings.json5`, `.env`（ただし本計画では `.env` を編集しない）

用語:

- 会話確定: ユーザーがボタンを押して「日記の区切り」を宣言する操作。
- セマンティック記憶: 日記の中に含まれる恒久的な知識・習慣・価値観。
- エピソード記憶: 日記の中の具体的な出来事や体験。
- 検索トグル: MiniRAG 検索の使用可否を切り替える UI スイッチ。

## Plan of Work

まずアーキテクチャ文書と avatar-ui のサービス設計を更新し、MiniRAG 連携がシステムのどこに位置づくかを明確化する。次に、F-AVATAR-001 の仕様・設計成果物を整備し、MiniRAG 登録データの構造と UI/サーバーの責務分担を確定する。最後に、実装のための具体的なファイルと変更内容を Impl Plan に記載し、品質ゲートを通過させる。

## Concrete Steps

1. アーキテクチャ文書の更新
   - `architecture/system-architecture.md` と `architecture/service-boundaries.md` に diary + MiniRAG 連携の責務を追記する。
   - `architecture/deployment-topology.md` に avatar-ui が外部の MiniRAG API を呼び出す前提を追記する。

2. avatar-ui サービス設計の更新
   - `services/avatar-ui/service-architecture.md` と `services/avatar-ui/README.ja.md` に新機能の説明と設定項目を追記する。
   - `services/avatar-ui/service-config.example.yaml` を作成し、MiniRAG 連携設定の例を示す。

3. 仕様・設計成果物の作成
   - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/` に spec/impl-plan/research/data-model/contracts/quickstart を作成する。
   - requirements と PlanQualityGate のチェックリストを埋める。

4. 品質ゲートとログの更新
   - `scripts/validate_spec.sh` と `scripts/validate_plan.sh` を新規チェックリストに対して実行する。
   - `harness/AI-Agent-progress.txt` と `docs/decisions.md` に結果と決定事項を記録する。

## Validation and Acceptance

- `scripts/validate_spec.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md` が PASSED を返す。
- `scripts/validate_plan.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/PlanQualityGate.md` が PASSED を返す。
- 新しい仕様書に「会話確定」「検索トグル」「MiniRAG 登録」「検索コンテキスト要件」が明記されている。

## Idempotence and Recovery

ドキュメント作成は再実行しても差分更新のみで済む。チェックリストが未完了の場合は該当項目を修正し、再度 validate スクリプトを実行することで復旧できる。

## Artifacts and Notes

- Epic design index: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`
  - Feature map（F-AVATAR-001）
  - MiniRAG 登録データの主要エンティティ
  - UI とサーバーの分担と交差フロー

## Interfaces and Dependencies

- MiniRAG API: `POST /minirag/documents/bulk`, `POST /minirag/search`
- avatar-ui Server: `POST /agui/diary/finalize`, `POST /agui/diary/search-settings`
- UI: search トグルと top_k 設定、会話確定ボタン、トランスクリプト送信
