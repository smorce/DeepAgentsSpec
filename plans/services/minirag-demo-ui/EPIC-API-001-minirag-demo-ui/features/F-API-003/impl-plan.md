# Implementation Plan: F-API-003

**Branch**: `F-API-003-minirag-chat-ui` | **Date**: 2026-01-02  
**Epic**: `EPIC-API-001-minirag-demo-ui` (`plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/exec-plan.md`)  
**Feature Spec**: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`  
**Spec Checklist**: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`  
**Plan Checklist**: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md` (validate via `scripts/validate_plan.sh`)  

**Input**: Feature specification under  
`plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`  
with a passing spec quality checklist at  
`plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`.

---

## Summary

ブラウザ上の静的な簡易チャットUIで、登録・検索・削除のデモ操作を可能にする。  
検索はチャット入力、登録/削除はボタン操作とし、結果は上位5件を関連度順で表示する。  
UI は `services/minirag/EPIC-API-001-minirag-demo-ui/frontend` で静的HTML/JSとして実装し、F-API-002 の REST API を呼び出す。

---

## Technical Context

**Language/Version**: HTML/CSS/Vanilla JS（ビルドなし）  
**Primary Services**: minirag/EPIC-API-001-minirag-demo-ui/frontend（UI）, api-gateway（バックエンド呼び出し）  
**Primary Dependencies**: なし（ブラウザ標準の fetch を使用）  
**Storage**: ブラウザのメモリ内のみ  
**Testing**: E2E（tests/e2e/ のシナリオ追加）  
**Target Environment**: ブラウザ + 最小HTTPサーバー（静的配信）  
**Project Type**: frontend-only（静的UI、バックエンド連携あり）  
**Performance Goals**: 主要操作は 3 分以内に完了できる（SC-001）  
**Constraints**: ビルドなし、固定デモ API キー、workspace は `demo` 固定、空入力は実行不可、エラーはチャット内表示、結果は上位5件、0件時は `note` 表示  
**Scale/Scope**: 単一ユーザーのデモ利用

---

## Constitution Check

- **Safety / Security**: OK（固定デモ API キーを使用、誤操作を抑止）
- **Maintainability**: OK（静的UI・契約・データモデルを整理）
- **Complexity / Scope Creep**: OK（新規サービスだが静的配信のみ）
- **Testing / Observability**: OK（E2E シナリオで主要導線を検証）

---

## Project Structure

### Documentation (this feature)

```text
plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/
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
plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/
├── exec-plan.md
└── design/
    └── index.md
```

### Source Code (repository root)

```text
services/
  frontend/
    EPIC-API-001-minirag-demo-ui/
      public/
        index.html
        style.css
        app.js
      scripts/
        run_dev.sh
```

**Structure Decision**:
静的配信の `public/` 配下に UI をまとめ、最小HTTPサーバーで配信する。E2E は `tests/e2e/scenarios` に追加する。

---

## Complexity Tracking

該当なし（静的UIのみ）。

---

## Plan of Work

- **Phase 0 – Research**: `research.md` で UI 実装位置と API 連携方針を確定
- **Phase 1 – Design & Contracts**: `data-model.md` / `contracts/ui-client-openapi.yaml` / `quickstart.md` を生成し、`design/index.md` を更新
- **Phase 2 – Implementation Prep**: `public/` 配下に UI を追加し、E2E シナリオを用意
- **Phase 3 – Validation**: `scripts/validate_spec.sh`, `scripts/validate_plan.sh`, `scripts/run_all_e2e_tests.sh`

---

## Concrete Steps

1. `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/research.md` を確認し、UI 実装と API 連携方針を固定する
2. `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/contracts/ui-client-openapi.yaml` を参照し、UI からの API 呼び出しを実装する
3. `services/minirag/EPIC-API-001-minirag-demo-ui/frontend/public/` に HTML/CSS/JS の UI を追加する
4. `tests/e2e/scenarios/minirag_demo_ui.spec.js` を追加し、登録→検索→削除とエラー表示を検証する
5. `checklists/PlanQualityGate.md` を埋め、`scripts/validate_plan.sh` を実行する

---

## Validation / Acceptance

- `scripts/validate_spec.sh plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md` → `PASSED`
- `scripts/validate_plan.sh plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md` → `PASSED`
- `scripts/run_all_e2e_tests.sh` → `PASS`
- UI 操作: 登録→検索→削除を 3 分以内に完了できる
- 空入力時はチャット内に注意メッセージが表示される

---

## Artifacts and Notes

- Epic design index: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/design/index.md`
  - UI 側の feature map と API 依存関係
  - F-API-002（api-gateway）との連携導線

---

## Idempotence / Recovery

- UI の状態は再読み込みで初期化される
- 誤登録時は削除操作でリセット可能
- チェックリスト誤更新は差し戻しで復旧可能

---

## Checklist & Gate Integration

- `checklists/requirements.md` と spec を同期し、`scripts/validate_spec.sh` で確認
- `checklists/PlanQualityGate.md` を維持し、`scripts/validate_plan.sh` の結果を `harness/AI-Agent-progress.txt` に記録
