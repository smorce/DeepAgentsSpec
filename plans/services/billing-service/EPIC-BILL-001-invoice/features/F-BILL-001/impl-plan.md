# Implementation Plan: F-BILL-001

**Branch**: `F-BILL-001-invoice-issuance` | **Date**: 2026-02-13  
**Epic**: `EPIC-BILL-001-INVOICE` (`plans/services/billing-service/EPIC-BILL-001-invoice/exec-plan.md`)  
**Feature Spec**: `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/spec.md`  
**Spec Checklist**: `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/requirements.md`  
**Plan Checklist**: `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/PlanQualityGate.md`

## Summary

注文情報を受け取り請求書を発行する API を実装するための最小実装計画。

## Technical Context

- Language/Version: Python 3.12（想定）
- Primary Dependencies: FastAPI/Pydantic（想定）
- Storage: 初期はインメモリ、将来 DB 置換可能
- Testing: unit + integration
- Target Platform: Linux container
- Project Type: backend microservice endpoint
- Performance Goals: 1 秒以内
- Constraints: 金額は非負、通貨は ISO 4217
- Scale/Scope: 単体サービスでの請求書発行

## Constitution Check

- Spec/Plan の品質ゲートを通過する
- 契約先行（OpenAPI）で実装に着手する
- テスト実行コマンドを統一する

## Project Structure

- `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/impl-plan.md`
- `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/research.md`
- `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/data-model.md`
- `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/contracts/openapi.yaml`
- `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/quickstart.md`
- `services/billing/EPIC-BILL-001-invoice/backend/`

## Complexity Tracking

- 税計算や外部連携は別 Feature に分割し、F-BILL-001 では扱わない。

## Plan of Work

1. 契約定義
2. 入力/出力モデル定義
3. 発行ハンドラ実装
4. テスト追加

## Concrete Steps

1. `contracts/openapi.yaml` に POST エンドポイントを定義
2. 請求書 ID 生成と入力検証を実装
3. `run_unit_tests.sh` / `run_integration_tests.sh` を更新
4. ハーネス共通スクリプトで回帰確認

## Validation / Acceptance

- `bash scripts/validate_spec.sh plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/requirements.md`
- `bash scripts/validate_plan.sh plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/PlanQualityGate.md`
- `bash scripts/run_all_unit_tests.sh`

## Idempotence / Recovery

- 再実行で同一注文IDの二重発行を防ぐ設計にする
- 失敗時は入力検証エラーとして返し、部分更新を残さない

## Artifacts and Notes

- `contracts/openapi.yaml`
- `data-model.md`
