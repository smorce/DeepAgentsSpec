# Feature Specification: Signup Page UI

**Feature ID**: F-USER-001  
**Epic**: EPIC-USER-001-ONBOARDING  
**Status**: Draft  
**Spec Checklist**: `plans/services/user-service/EPIC-USER-001-onboarding/features/F-USER-001/checklists/requirements.md`

## Overview

ユーザー登録のための最小 UI を提供し、`email/password` を入力して送信できることを目標とする。

## In Scope

- `/signup` 画面表示
- 入力欄: email / password
- 送信ボタンと結果表示領域

## Out of Scope

- OAuth / SNS ログイン
- 多要素認証

## Functional Requirements

- FR-USER-001-001: `/signup` でフォームを表示する
- FR-USER-001-002: 必須入力欠落時にエラー表示する
- FR-USER-001-003: 有効入力時に `POST /api/users` を呼ぶ

## Non-Functional Requirements

- NFR-USER-001-001: フォーム表示は 2 秒以内
- NFR-USER-001-002: エラー表示はユーザーに理解可能な文言

## References

- `plans/services/user-service/EPIC-USER-001-onboarding/exec-plan.md`
- `architecture/service-boundaries.md`

## Success Criteria

- SC-USER-001-001: Signup フォームが表示される
- SC-USER-001-002: 正常入力で成功通知が表示される
