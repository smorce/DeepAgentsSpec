# Quickstart: F-USER-001

## 1. Gate

```bash
bash scripts/validate_spec.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md
bash scripts/validate_plan.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/PlanQualityGate.md
```

## 2. Test

```bash
bash scripts/run_all_unit_tests.sh
bash scripts/run_all_e2e_tests.sh
```

## 3. Manual Check

- `http://localhost:8080/signup` を開く
- email/password を入力し送信
