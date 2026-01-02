# Exec Plan: EPIC-API-001-MINIRAG-DEMO-UI

このExecPlanは常に更新される生きたドキュメントです。`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を作業の進行に合わせて維持します。  
本ドキュメントは `PLANS.md` に従って維持・更新されます。

本エピックの設計インデックスは `plans/services/frontend/EPIC-API-001-minirag-demo-ui/design/index.md` にあります。ここには feature map、共有エンティティ、共有API、クロスフローの要約がまとまっています。

## Purpose / Big Picture

MiniRAG デモの UI を静的HTML/JSで提供し、利用者が「登録→検索→削除」をブラウザで直感的に操作できるようにする。完成後は最小のHTTPサーバーで配信し、F-API-002（api-gateway）の API を呼び出して結果を確認できる状態になる。

## Related Features / Specs

- F-API-003: MiniRAGデモ用チャットUI  
  Spec: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`

## Progress

- [x] (2026-01-02 03:15Z) F-API-003 の plan 品質ゲートを通過
- [ ] F-API-003 の tasks.md 生成
- [ ] F-API-003 の実装（静的UI追加）
- [ ] F-API-003 のE2E検証とログ記録

## Surprises & Discoveries

- Observation: 特になし。進捗に伴い追記する。

## Decision Log

- Decision: UI は静的HTML/JSのみで提供し、ビルド工程は設けない。  
  Rationale: デモ用途で最小構成・最短導線を優先。  
  Date/Author: 2026-01-02 / Codex
- Decision: UI は固定デモAPIキーを埋め込み、F-API-002 の REST API を直接呼ぶ。  
  Rationale: 操作の簡潔さと安全性の最小バランス。  
  Date/Author: 2026-01-02 / Codex

## Outcomes & Retrospective

- 現時点では計画フェーズ完了。実装と検証は未着手。

## Context and Orientation

本エピックは `services/frontend/EPIC-API-001-minirag-demo-ui` 配下で静的UIを提供する。UI は `public/` 配下のHTML/JS/CSSで構成し、最小HTTPサーバーで配信する。バックエンドは `services/api-gateway` の MiniRAG API（F-API-002）を利用する。

関連ファイルは以下の通り。

- F-API-003 spec: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`
- F-API-003 impl-plan: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/impl-plan.md`
- F-API-003 design artifacts: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/{research.md,data-model.md,contracts/,quickstart.md}`

## Plan of Work

まず `impl-plan.md` に従い、静的UIの構成と API 連携方針を確認する。次に `public/` 配下へ HTML/JS/CSS を追加し、登録・検索・削除の操作と結果表示を実装する。最後に E2E シナリオを追加して、UI 操作が一連で確認できることを検証する。

## Concrete Steps

1. `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/impl-plan.md` を読み、作業対象ファイルを確認する。
2. `services/frontend/EPIC-API-001-minirag-demo-ui/public/` に `index.html` / `style.css` / `app.js` を追加する。
3. `tests/e2e/scenarios/minirag_demo_ui.spec.js` を追加し、登録→検索→削除を検証する。
4. `scripts/run_all_e2e_tests.sh` を更新し、新しいシナリオを実行できるようにする。

## Validation and Acceptance

- `scripts/validate_spec.sh plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md` が `PASSED` を返す。
- `scripts/validate_plan.sh plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md` が `PASSED` を返す。
- `scripts/run_all_e2e_tests.sh` が `PASS` を返す。
- ブラウザ操作で「登録→検索→削除」が 3 分以内に完了できる。

## Idempotence and Recovery

- 静的ファイルの差し替えは安全に再実行できる。
- 誤登録は削除操作で復旧できる。
- 失敗したテストは対象シナリオを修正して再実行する。

## Artifacts and Notes

- Epic design index: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/design/index.md`
  - Feature map（F-API-003）
  - 共有エンティティとAPI（F-API-002 依存）
  - クロスフロー（登録→検索→削除）

Feature artifacts:

- F-API-003:
  - Spec: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`
  - Impl plan: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/impl-plan.md`
  - Data model: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/data-model.md`
  - Contracts: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/contracts/`
  - Quickstart: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/quickstart.md`

## Interfaces and Dependencies

UI は `X-Demo-Api-Key` ヘッダを付与して `POST /minirag/search`、`POST /minirag/documents/bulk`、`DELETE /minirag/documents`、`DELETE /minirag/documents/{doc_id}` を呼び出す。検索結果は上位5件を表示し、0件時は空配列＋注記を表示する。バックエンドは F-API-002 の API を使用する。

---

変更履歴: 2026-01-02 に UI 専用エピックとして ExecPlan を作成。理由は新規サービスで静的UIを提供するため。
