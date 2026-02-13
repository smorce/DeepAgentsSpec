# Implementation Plan: F-USER-002

**Branch**: `F-USER-002-signup-api` | **Date**: 2026-02-13  
**Epic**: `EPIC-USER-001-ONBOARDING` (`plans/services/user-service/EPIC-USER-001-onboarding/exec-plan.md`)  
**Feature Spec**: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/spec.md`  
**Spec Checklist**: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/requirements.md`  
**Plan Checklist**: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/PlanQualityGate.md`

## Summary

`POST /api/users` を実装し、signup UI から利用可能なユーザー登録 API を提供する。

## Technical Context

- Language/Version: Python 3.12（想定）
- Primary Dependencies: FastAPI/Pydantic（想定）
- Storage: 初期はインメモリ、将来 DB 置換
- Testing: unit + integration
- Target Platform: Linux container
- Project Type: backend API
- Performance Goals: 1 秒以内
- Constraints: email 一意、password 最小長、エラーコード統一
- Scale/Scope: onboarding 用単一エンドポイント

## Constitution Check

- 契約先行（OpenAPI）
- Spec/Plan ゲートの実行ログを progress へ記録
- TDD（失敗テストから開始）を維持

## Project Structure

- `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/impl-plan.md`
- `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/research.md`
- `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/data-model.md`
- `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/contracts/openapi.yaml`
- `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/quickstart.md`
- `services/user/EPIC-USER-001-onboarding/backend/`

## Complexity Tracking

- 認証トークン発行は別 Feature に分離する。

## Plan of Work

1. API 契約定義
2. 入力検証モデル定義
3. create user ハンドラ
4. 重複検知とエラー応答

## Concrete Steps

1. `contracts/openapi.yaml` を作成
2. DTO / バリデーション実装
3. handler/service/repository を分離
4. unit/integration テスト追加

## Validation / Acceptance

- `bash scripts/validate_spec.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/requirements.md`
- `bash scripts/validate_plan.sh plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/PlanQualityGate.md`
- `bash scripts/run_all_unit_tests.sh`
- `curl -X POST http://localhost:8080/api/users -H 'Content-Type: application/json' -d '{"email":"test@example.com","password":"password123"}'`

## Idempotence / Recovery

- 重複 email は 409 で返しデータ破損を防ぐ
- 失敗時は永続化を行わず再試行可能にする

## Artifacts and Notes

- `contracts/openapi.yaml`
- `data-model.md`
