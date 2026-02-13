# Feature Specification: Signup API Endpoint

**Feature ID**: F-USER-002  
**Epic**: EPIC-USER-001-ONBOARDING  
**Status**: Draft  
**Spec Checklist**: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-002/checklists/requirements.md`

## Overview

`POST /api/users` を提供し、メールアドレスとパスワードで新規ユーザーを作成する。

## In Scope

- API エンドポイント `POST /api/users`
- 入力検証
- 成功/失敗の標準レスポンス

## Out of Scope

- メール認証フロー
- 認可トークン発行

## Functional Requirements

- FR-USER-002-001: 有効入力でユーザー作成できる
- FR-USER-002-002: 重複 email は 409 を返す
- FR-USER-002-003: 不正入力は 400 を返す

## Non-Functional Requirements

- NFR-USER-002-001: 正常応答は 1 秒以内
- NFR-USER-002-002: エラーメッセージは機械可読な JSON

## References

- `plans/services/user-service/EPIC-USER-001-onboarding/exec-plan.md`
- `architecture/service-boundaries.md`

## Success Criteria

- SC-USER-002-001: 正常系で 201 + user_id
- SC-USER-002-002: 異常系で 400/409 + error_code
