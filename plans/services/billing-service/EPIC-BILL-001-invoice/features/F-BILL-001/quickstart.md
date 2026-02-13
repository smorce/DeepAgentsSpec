# Quickstart: F-BILL-001

## 1. Gate

```bash
bash scripts/validate_spec.sh plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/requirements.md
bash scripts/validate_plan.sh plans/services/billing-service/EPIC-BILL-001-invoice/features/F-BILL-001/checklists/PlanQualityGate.md
```

## 2. Test

```bash
bash scripts/run_all_unit_tests.sh
```

## 3. API Check (example)

```bash
curl -X POST http://localhost:8082/billing/invoices \
  -H 'Content-Type: application/json' \
  -d '{"order_id":"ord-001","customer_id":"cus-001","items":[{"sku":"SKU-1","quantity":1,"unit_price":1000}]}'
```
