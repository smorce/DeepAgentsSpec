# Quickstart: F-USER-002

## 1. Gate

```bash
bash scripts/validate_spec.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/requirements.md
bash scripts/validate_plan.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/PlanQualityGate.md
```

## 2. Test

```bash
bash scripts/run_all_unit_tests.sh
```

## 3. API Check

```bash
curl -X POST http://localhost:8080/api/users \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password123"}'
```
