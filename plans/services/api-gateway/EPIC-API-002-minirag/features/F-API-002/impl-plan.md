# Implementation Plan: F-API-002

**Branch**: `F-API-002-minirag-backend` | **Date**: 2026-01-02  
**Epic**: `EPIC-API-002-minirag` (`plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md`)  
**Feature Spec**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`  
**Plan Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md` (validate via `scripts/validate_plan.sh`)  

**Input**: Feature specification under  
`plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`  
with a passing spec quality checklist at  
`plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`.

---

## Summary

MiniRAG を用いた構造化データの登録・検索・削除 API を api-gateway に追加する。  
デモ利用者が 5 件のサンプルデータを登録し、検索結果（上位3件に関連結果）と削除反映を確認できることを成功基準とする。  
技術的には、MiniRAG の参考実装に合わせた Python 実装を採用し、PostgreSQL + pgvector を永続化層として利用する。

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Services**: api-gateway  
**Primary Dependencies**: FastAPI, MiniRAG, psycopg/asyncpg, pgvector  
**Storage**: PostgreSQL（pgvector 有効化）  
**Testing**: pytest（API ハンドラの単体テスト）＋ E2E シナリオ  
**Target Environment**: ローカル環境で再現可能な起動（Docker/compose 想定）  
**Project Type**: backend-only  
**Performance Goals**: 検索結果が 3 秒以内に返る（NFR-001）  
**Constraints**: 固定デモ API キー必須、0件時は空配列＋注記、Upsert、削除件数返却  
**Scale/Scope**: デモ用途の単一ユーザー、固定 5 件のサンプルを対象

---

## Constitution Check

- **Safety / Security**: OK（固定デモ API キー必須、依存障害時のエラーハンドリングを明記）
- **Maintainability**: OK（仕様・計画・契約・データモデルを明確化し、Tidy First に従う）
- **Complexity / Scope Creep**: OK（単一サービス内で完結、追加サービスなし）
- **Testing / Observability**: OK（単体＋E2Eテストを計画、失敗時はユーザー向けエラー表示）

---

## Project Structure

### Documentation (this feature)

```text
plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/
├── spec.md               # Feature specification (/speckit.specify output)
├── impl-plan.md          # This file (/speckit.plan output)
├── research.md           # Phase 0 output (/speckit.plan)
├── data-model.md         # Phase 1 output (/speckit.plan)
├── quickstart.md         # Phase 1 output (/speckit.plan)
├── contracts/            # Phase 1 output (/speckit.plan) - API / schema contracts
├── checklists/
│   ├── requirements.md    # Spec quality checklist (/speckit.specify + scripts/validate_spec.sh)
│   └── PlanQualityGate.md # Plan quality checklist (/speckit.plan + scripts/validate_plan.sh)
└── tasks.md              # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Epic-level Design (cross-feature context)

```text
plans/services/api-gateway/EPIC-API-002-minirag/
├── exec-plan.md          # Epic-level execution plan (required)
└── design/
    └── index.md          # Lightweight design index (optional but recommended)
```

### Source Code (repository root)

```text
services/
  api-gateway/
    src/
      minirag/
        service.py
        repository.py
        schemas.py
      routes/
        minirag.py
    tests/
      test_minirag_routes.py

tests/
  e2e/
    scenarios/
      minirag_demo.spec.js
```

**Structure Decision**:
api-gateway 単独で実装し、`src/minirag` と `src/routes/minirag.py` に機能を集約する。E2E は `tests/e2e/scenarios` に追加。

---

## Complexity Tracking

該当なし（新規サービス追加なし）。

---

## Plan of Work

- **Phase 0 – Research**: `research.md` に DB/LLM/認可/エンドポイント方針を整理済み
- **Phase 1 – Design & Contracts**: `data-model.md` / `contracts/openapi.yaml` / `quickstart.md` を生成し、`design/index.md` を更新
- **Phase 2 – Implementation Prep**: api-gateway のルーティングと MiniRAG 連携を追加し、単体テストとE2Eを準備
- **Phase 3 – Validation**: `scripts/validate_spec.sh`, `scripts/validate_plan.sh`, `scripts/run_all_unit_tests.sh`, `scripts/run_all_e2e_tests.sh`

---

## Concrete Steps

1. `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/research.md` を確認し、設計判断を確定する
2. `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/contracts/openapi.yaml` を API 実装のソースオブトゥルースにする
3. `services/api-gateway/src/minirag/` と `services/api-gateway/src/routes/minirag.py` を追加し、登録・検索・削除 API を実装する
4. `services/api-gateway/tests/test_minirag_routes.py` に単体テストを追加する
5. `tests/e2e/scenarios/minirag_demo.spec.js` に登録→検索→削除のシナリオを追加する
6. `scripts/run_all_unit_tests.sh` / `scripts/run_all_e2e_tests.sh` を更新し、実行可能にする
7. `checklists/PlanQualityGate.md` を埋め、`scripts/validate_plan.sh` を実行する

---

## Validation / Acceptance

- `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md` → `PASSED`
- `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md` → `PASSED`
- `scripts/run_all_unit_tests.sh` → `PASS`
- `scripts/run_all_e2e_tests.sh` → `PASS`
- `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/documents/bulk ...` → 200
- `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/search ...` → 200 (0件時は note="0件")

---

## Artifacts and Notes

- Epic design index: `plans/services/api-gateway/EPIC-API-002-minirag/design/index.md`
  - 共有エンティティと API のマップ
  - F-API-003 との連携導線

---

## Idempotence / Recovery

- 登録は Upsert のため再実行しても安全
- 失敗時は `DELETE /minirag/documents?workspace=...` で全削除し再登録
- DB 側の初期化が必要な場合は、デモ用スキーマを再作成してから再実行
- チェックリスト誤更新は差し戻しで復旧可能

---

## Checklist & Gate Integration

- `checklists/requirements.md` と spec を同期し、`scripts/validate_spec.sh` で確認
- `checklists/PlanQualityGate.md` を維持し、`scripts/validate_plan.sh` の結果を `harness/AI-Agent-progress.txt` に記録
