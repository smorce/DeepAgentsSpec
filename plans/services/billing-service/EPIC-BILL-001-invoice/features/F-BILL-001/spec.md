# Feature Specification: Billing Invoice Issuance API

**Feature ID**: F-BILL-001  
**Epic**: EPIC-BILL-001-INVOICE  
**Status**: Draft  
**Spec Checklist**: `plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/requirements.md`

## Overview

請求書発行 API を定義し、注文単位で請求書を生成できる最小機能を提供する。

## In Scope

- `POST /billing/invoices` による請求書作成
- 請求書ID、金額、通貨、発行日時の返却
- 入力検証（order_id, customer_id, items）

## Out of Scope

- 税計算の高度ロジック
- 外部会計システム連携

## Functional Requirements

- FR-BILL-001-001: 有効入力で請求書を発行できる
- FR-BILL-001-002: 無効入力で 400 を返す
- FR-BILL-001-003: 発行結果に invoice_id を含める

## Non-Functional Requirements

- NFR-BILL-001-001: API 応答は 1 秒以内
- NFR-BILL-001-002: 監査用に created_at を返す

## References

- `architecture/system-architecture.md`
- `plans/services/billing-service/EPIC-BILL-001-invoice/exec-plan.md`

## Success Criteria

- SC-BILL-001-001: 正常系で HTTP 201
- SC-BILL-001-002: 異常系で HTTP 400 とエラー詳細
