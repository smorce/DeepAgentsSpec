# Data Model: F-API-001

## Entity: HealthStatus

- status: string (`ok` 固定)
- service: string (`api-gateway` 固定)
- timestamp: string (ISO8601, optional)

## Validation Rules

- status は空文字不可
- service は空文字不可
- timestamp を返す場合は UTC ISO8601
