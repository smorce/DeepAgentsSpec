# Quickstart: F-API-001

## 1. Spec / Plan Gate

```bash
bash scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/requirements.md
bash scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/PlanQualityGate.md
```

## 2. Unit Test

```bash
bash scripts/run_all_unit_tests.sh
```

## 3. Manual Check

```bash
curl -s http://localhost:8080/health
```
