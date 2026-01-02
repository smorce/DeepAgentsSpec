# Exec Plan: EPIC-API-002-MINIRAG

このExecPlanは常に更新される生きたドキュメントです。`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を作業の進行に合わせて維持します。  
本ドキュメントは `PLANS.md` に従って維持・更新されます。

このエピック配下には、現時点の作業ツリーでは `plans/services/api-gateway/EPIC-API-002-minirag/design/index.md` が存在しません。設計インデックスを作成する場合は、後続の更新で `Artifacts and Notes` にそのパスと役割を明記します。

## Purpose / Big Picture

MiniRAG を使ったデモで、利用者が「構造化データの登録→検索→削除」を一連で体験できるようにする。完成後は、API と UI の双方からデモが再現でき、検索結果の妥当性と削除の反映が短時間で確認できる状態になる。

## Related Features / Specs

このエピックに紐づく機能仕様は以下の2つ。

- F-API-002: MiniRAG構造化データ登録・検索バックエンド  
  Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`
- F-API-003: MiniRAGデモ用チャットUI  
  Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/spec.md`  
  注意: 本ブランチには当該 spec が存在しないため、必要なら F-API-003 ブランチから取得する。

## Progress

- [x] (2026-01-02 02:49Z) F-API-002 の spec 品質ゲートを通過
- [x] (2026-01-02 03:16Z) F-API-002 の plan 品質ゲートを通過
- [ ] F-API-002 の実装タスク分解（`/speckit.tasks`）と Issue 化
- [ ] F-API-002 の TDD 実装（Red→Green→Refactor）
- [ ] F-API-003 の plan 品質ゲート確認（F-API-003 ブランチ側）
- [ ] F-API-003 の実装タスク分解と TDD 実装

## Surprises & Discoveries

- Observation: 特になし。進捗に伴い追記する。

## Decision Log

- Decision: 登録は Upsert、0件検索は空配列＋注記、削除は件数返却。  
  Rationale: デモ利用時の再実行性と分かりやすさを優先。  
  Date/Author: 2026-01-02 / Codex
- Decision: 認可は固定デモAPIキーを必須とする。  
  Rationale: 最小限の安全策として十分で、デモの手順を複雑化しない。  
  Date/Author: 2026-01-02 / Codex

## Outcomes & Retrospective

- 現時点では計画フェーズ完了。実装と検証は未着手。

## Context and Orientation

このエピックは api-gateway を中心に MiniRAG の登録・検索・削除 API を追加し、UI から操作可能にする。主要な仕様と計画は以下の場所にある。

- F-API-002 spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`
- F-API-002 impl-plan: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/impl-plan.md`
- F-API-002 research/data/contract: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/{research.md,data-model.md,contracts/}`

UI 側の F-API-003 は別ブランチで計画済み。該当する spec/plan は同じエピック配下パスに存在する前提で、UI 実装は `services/avatar-ui/app/src/renderer/` を想定する。

## Plan of Work

まず F-API-002 の実装計画に従い、API の登録・検索・削除の振る舞いを api-gateway に追加する。次にテスト（単体/E2E）を追加して API の振る舞いを検証する。F-API-003 は UI 側のブランチで、チャットUIの操作導線と API 呼び出しの実装を行う。各フェーズで、`scripts/validate_spec.sh` と `scripts/validate_plan.sh` のゲート結果を `harness/AI-Agent-progress.txt` に残す。

## Concrete Steps

1. `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/impl-plan.md` を参照し、api-gateway に MiniRAG 連携の実装タスクを `/speckit.tasks` で切り出す。
2. `services/api-gateway/src/` 配下に MiniRAG 連携のモジュールとルートを追加し、登録・検索・削除 API を実装する。
3. `services/api-gateway/tests/` と `tests/e2e/scenarios/` にテストを追加し、`scripts/run_all_unit_tests.sh` / `scripts/run_all_e2e_tests.sh` を通す。
4. UI 側（F-API-003 ブランチ）でチャットUIと API 呼び出しを実装し、E2E シナリオで連携を確認する。

## Validation and Acceptance

- `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md` が `PASSED` を返す。
- `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md` が `PASSED` を返す。
- API 起動後、以下の操作で 200 が返り、結果が確認できる。

  `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/documents/bulk ...`

  `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/search ...`

- UI 操作で「登録→検索→削除」が 3 分以内に完了できる。

## Idempotence and Recovery

- 登録は Upsert のため再実行しても安全。
- 失敗時は `DELETE /minirag/documents?workspace=...` で全削除し再登録。
- テスト追加は繰り返し実行可能。失敗時は対象テストのみ修正して再実行する。

## Artifacts and Notes

現時点のこのブランチでは epic design index は未作成。作成する場合は以下の情報を必ず記載する。

- Feature map（F-API-002 / F-API-003 の一覧）
- 共有エンティティ（StructuredDocument / SearchResult）
- 共有 API（/minirag/search など）
- クロスフロー（登録→検索→削除）

Feature artifacts:

- F-API-002:
  - Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`
  - Impl plan: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/impl-plan.md`
  - Data model: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/data-model.md`
  - Contracts: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/contracts/`
  - Quickstart: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/quickstart.md`

## Interfaces and Dependencies

API は `X-Demo-Api-Key` を必須ヘッダとして受け付ける。登録・検索・削除は `/minirag` 配下に集約し、入力は JSON を前提とする。検索は関連度付きで結果を返し、0件のときは空配列と注記を返す。削除は削除件数を返す。UI 側はこれらのエンドポイントを直接呼び出し、結果をチャット履歴に表示する。

---

変更履歴: 2026-01-02 に ExecPlan を PLANS.md のテンプレートに合わせて詳細化。理由は epic の進行状況と設計成果物の場所を自己完結的に示すため。
