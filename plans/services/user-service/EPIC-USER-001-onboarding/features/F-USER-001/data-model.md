# Data Model: F-USER-001

## Entity: SignupFormState

- email: string
- password: string
- submit_status: enum(`idle`,`submitting`,`success`,`error`)
- error_message: string | null

## Validation Rules

- email は RFC 準拠形式
- password は最小 8 文字
