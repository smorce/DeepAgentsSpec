# Implementation Plan: F-API-001

**Branch**: `F-API-001-health` | **Date**: 2026-02-13  
**Epic**: `EPIC-API-001-ROUTING` (`plans/services/api-gateway/EPIC-API-001-routing/exec-plan.md`)  
**Feature Spec**: `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/spec.md`  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/requirements.md`  
**Plan Checklist**: `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/PlanQualityGate.md`

## Summary

API Gateway に `GET /health` を実装し、監視対象として最小の安定エンドポイントを提供する。

## Technical Context

- Language/Version: Python 3.12（想定）
- Primary Dependencies: FastAPI または同等HTTPフレームワーク（既存実装に追従）
- Storage: なし
- Testing: unit test（ハンドラ応答）
- Target Platform: Linux container
- Project Type: backend microservice endpoint
- Performance Goals: 800ms 未満
- Constraints: 副作用なし、認証不要、JSON固定
- Scale/Scope: 監視用途の単一エンドポイント

## Constitution Check

- Spec/Plan ゲートを通す
- 実装前に契約を `contracts/openapi.yaml` で固定
- テストは `scripts/run_all_unit_tests.sh` に接続

## Project Structure

- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/impl-plan.md`
- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/research.md`
- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/data-model.md`
- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/contracts/openapi.yaml`
- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/quickstart.md`

## Complexity Tracking

- 追加複雑性は低い。将来の詳細ヘルスチェックは別 Feature に分離する。

## Plan of Work

1. 契約を定義する
2. ハンドラを追加する
3. unit テストを追加する
4. `scripts/run_all_unit_tests.sh` 経由で検証する

## Concrete Steps

1. `contracts/openapi.yaml` で `GET /health` を定義
2. API Gateway ハンドラを追加
3. テストで `status/service` を検証
4. 品質ゲート実行結果を `harness/AI-Agent-progress.txt` に記録

## Validation / Acceptance

- `bash scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/requirements.md`
- `bash scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/PlanQualityGate.md`
- `bash scripts/run_all_unit_tests.sh`
- `curl -s http://localhost:8080/health | jq '.status,.service'`

## Idempotence / Recovery

- ハンドラは再デプロイしても副作用なし
- 失敗時はハンドラ差分を巻き戻し、テスト再実行で復旧可能

## Artifacts and Notes

- `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/contracts/openapi.yaml`
