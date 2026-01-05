# Quickstart: F-API-003 MiniRAGデモ用チャットUI

## 目的
静的HTML/JSの簡易チャットUIで、登録・検索・削除のデモ操作を行えるようにする。

## 実装想定位置
- `services/minirag/EPIC-API-001-minirag-demo-ui/frontend/public/` 配下に UI を配置
- E2E シナリオは `tests/e2e/scenarios/` に追加

## 主要アーティファクト
- Spec: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`
- Checklist: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`
- Research: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/research.md`
- Data Model: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/data-model.md`
- Contracts: `plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/contracts/ui-client-openapi.yaml`

## UI 要件の要約
- 検索はチャット入力で実行
- 登録/削除はボタン操作
- 結果は上位5件を関連度順で表示（0件時は `note: "0件"` を表示）
- エラーはチャット履歴内に表示
- 空入力は実行せず注意メッセージを表示
- 静的配信（ビルドなし）
- workspace は固定値 `demo`
- 登録完了時は `registered_count` を表示

## バリデーション
- `scripts/validate_spec.sh plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`
- `scripts/validate_plan.sh plans/services/minirag-demo-ui/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md`
- `scripts/run_all_e2e_tests.sh`
