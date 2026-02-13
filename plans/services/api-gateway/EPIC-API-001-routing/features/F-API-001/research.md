# Research: F-API-001

## Decision 1: Health endpoint shape

- Decision: `GET /health` はシンプルな JSON 応答を返す
- Rationale: LB / 監視ツールとの互換性が高い
- Alternatives considered:
  - plain text: 情報量が不足
  - deep health check: 初期フェーズには過剰

## Decision 2: Authentication policy

- Decision: 認証不要
- Rationale: 生存確認の可用性を優先
- Alternatives considered:
  - API key 必須: 監視導入が煩雑になる
