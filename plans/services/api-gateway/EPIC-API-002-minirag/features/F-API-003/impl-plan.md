# Implementation Plan: F-API-003

**Branch**: `F-API-002-minirag-backend` | **Date**: 2026-01-02  
**Epic**: `EPIC-API-002-minirag` (`plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md`)  
**Feature Spec**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/spec.md`  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md`  
**Plan Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/PlanQualityGate.md` (validate via `scripts/validate_plan.sh`)  

**Input**: Feature specification under  
`plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/spec.md`  
with a passing spec quality checklist at  
`plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md`.

---

## Summary

ブラウザ上の簡易チャットUIで、登録・検索・削除のデモ操作を可能にする。  
検索はチャット入力、登録/削除はボタン操作とし、結果は上位5件を関連度順で表示する。  
UI は avatar-ui のフロントエンド（Vite/Electron）に実装し、F-API-002 の REST API を呼び出す。

---

## Technical Context

**Language/Version**: TypeScript 5.x  
**Primary Services**: avatar-ui（UI）, api-gateway（バックエンド呼び出し）  
**Primary Dependencies**: Vite, Electron, @ag-ui/client（既存依存）  
**Storage**: ブラウザのメモリ内のみ  
**Testing**: E2E（tests/e2e/ のシナリオ追加）  
**Target Environment**: ブラウザ（Vite dev）および Electron  1プロセス  
**Project Type**: frontend-only（バックエンド連携あり）  
**Performance Goals**: 主要操作は 3 分以内に完了できる（SC-001）  
**Constraints**: 固定デモ API キー埋め込み、空入力は実行不可、エラーはチャット内表示、結果は上位5件  
**Scale/Scope**: 単一ユーザーのデモ利用

---

## Constitution Check

- **Safety / Security**: OK（固定デモ API キーを使用、誤操作を抑止）
- **Maintainability**: OK（UI/契約/データモデルを整理、既存構成に沿う）
- **Complexity / Scope Creep**: OK（既存 UI サービス内で完結）
- **Testing / Observability**: OK（E2E シナリオで主要導線を検証）

---

## Project Structure

### Documentation (this feature)

```text
plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/
├── spec.md
├── impl-plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── checklists/
│   ├── requirements.md
│   └── PlanQualityGate.md
└── tasks.md
```

### Epic-level Design (cross-feature context)

```text
plans/services/api-gateway/EPIC-API-002-minirag/
├── exec-plan.md
└── design/
    └── index.md
```

### Source Code (repository root)

```text
services/
  avatar-ui/
    app/
      src/
        renderer/
          minirag/
            api.ts
            components.ts
          main.ts
          style.css

tests/
  e2e/
    scenarios/
      minirag_demo_ui.spec.js
```

**Structure Decision**:
avatar-ui の renderer 配下に MiniRAG 専用 UI を追加し、既存 `main.ts` から初期化する。E2E は `tests/e2e/scenarios` に追加する。

---

## Complexity Tracking

該当なし（新規サービス追加なし）。

---

## Plan of Work

- **Phase 0 – Research**: `research.md` で UI 実装位置と API 連携方針を確定
- **Phase 1 – Design & Contracts**: `data-model.md` / `contracts/ui-client-openapi.yaml` / `quickstart.md` を生成し、`design/index.md` を更新
- **Phase 2 – Implementation Prep**: renderer 配下に UI を追加し、E2E シナリオを用意
- **Phase 3 – Validation**: `scripts/validate_spec.sh`, `scripts/validate_plan.sh`, `scripts/run_all_e2e_tests.sh`

---

## Concrete Steps

1. `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/research.md` を確認し、UI 実装と API 連携方針を固定する
2. `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/contracts/ui-client-openapi.yaml` を参照し、UI からの API 呼び出しを実装する
3. `services/avatar-ui/app/src/renderer/minirag/` に UI 部品と API クライアントを追加する
4. `services/avatar-ui/app/src/renderer/main.ts` に MiniRAG UI の初期化を組み込む
5. `tests/e2e/scenarios/minirag_demo_ui.spec.js` を追加し、登録→検索→削除とエラー表示を検証する
6. `checklists/PlanQualityGate.md` を埋め、`scripts/validate_plan.sh` を実行する

---

## Validation / Acceptance

- `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md` → `PASSED`
- `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/PlanQualityGate.md` → `PASSED`
- `scripts/run_all_e2e_tests.sh` → `PASS`
- UI 操作: 登録→検索→削除を 3 分以内に完了できる
- 空入力時はチャット内に注意メッセージが表示される

---

## Artifacts and Notes

- Epic design index: `plans/services/api-gateway/EPIC-API-002-minirag/design/index.md`
  - 共有エンティティと API のマップ
  - F-API-002 との連携導線

---

## Idempotence / Recovery

- UI の状態は再読み込みで初期化される
- 誤登録時は削除操作でリセット可能
- チェックリスト誤更新は差し戻しで復旧可能

---

## Checklist & Gate Integration

- `checklists/requirements.md` と spec を同期し、`scripts/validate_spec.sh` で確認
- `checklists/PlanQualityGate.md` を維持し、`scripts/validate_plan.sh` の結果を `harness/AI-Agent-progress.txt` に記録
