# Data Model: F-USER-002

## Entity: User

- user_id: string
- email: string (unique)
- password_hash: string
- created_at: string (ISO8601)

## Entity: SignupRequest

- email: string
- password: string

## Entity: SignupResponse

- user_id: string
- email: string

## Validation Rules

- email は RFC 準拠形式
- password は最小 8 文字
- email 重複時は 409
