# Research: F-BILL-001

## Decision 1: Initial storage strategy

- Decision: 初期はインメモリ管理で始める
- Rationale: 契約とユースケース検証を先行できる
- Alternatives considered:
  - 先に RDB を導入: 初期コストが高い

## Decision 2: Invoice ID format

- Decision: `inv_<timestamp>_<random>` 形式を採用
- Rationale: 一意性を確保し、ログ追跡しやすい
- Alternatives considered:
  - UUID only: 可読性が低い
