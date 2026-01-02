# Quickstart: F-API-002 MiniRAG構造化データ登録・検索バックエンド

## 目的
デモ用の構造化データ登録・検索・削除APIを api-gateway に追加するための最短手順を示す。

## 実装想定位置
- `services/api-gateway/src/` 配下に MiniRAG 用のハンドラ/ルータを追加
- `services/api-gateway/tests/` に単体テストを追加
- `tests/e2e/scenarios/` にE2Eシナリオを追加

## 主要アーティファクト
- Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`
- Checklist: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`
- Research: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/research.md`
- Data Model: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/data-model.md`
- Contracts: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/contracts/openapi.yaml`

## 想定API（抜粋）
- `POST /minirag/documents/bulk`
- `POST /minirag/search`
- `DELETE /minirag/documents/{doc_id}`
- `DELETE /minirag/documents?workspace=...`

## 実装・検証の流れ
1. api-gateway に MiniRAG 連携モジュールを追加
2. DB 接続とベクトル検索の初期化を行う
3. APIキー（`X-Demo-Api-Key`）を必須化
4. 登録・検索・削除 API を実装
5. 単体テストと E2E シナリオを追加

## バリデーション
- `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`
- `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md`
- `scripts/run_all_unit_tests.sh`
- `scripts/run_all_e2e_tests.sh`
