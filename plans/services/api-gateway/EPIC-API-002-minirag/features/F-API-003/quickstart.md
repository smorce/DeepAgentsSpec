# Quickstart: F-API-003 MiniRAGデモ用チャットUI

## 目的
ブラウザ上の簡易チャットUIで、登録・検索・削除のデモ操作を行えるようにする。

## 実装想定位置
- `services/avatar-ui/app/src/renderer/` 配下に UI を追加
- `services/avatar-ui/app/src/renderer/main.ts` から UI を初期化
- E2E シナリオは `tests/e2e/scenarios/` に追加

## 主要アーティファクト
- Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/spec.md`
- Checklist: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md`
- Research: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/research.md`
- Data Model: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/data-model.md`
- Contracts: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/contracts/ui-client-openapi.yaml`

## UI 要件の要約
- 検索はチャット入力で実行
- 登録/削除はボタン操作
- 結果は上位5件を関連度順で表示
- エラーはチャット履歴内に表示
- 空入力は実行せず注意メッセージを表示

## バリデーション
- `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md`
- `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/PlanQualityGate.md`
- `scripts/run_all_e2e_tests.sh`
