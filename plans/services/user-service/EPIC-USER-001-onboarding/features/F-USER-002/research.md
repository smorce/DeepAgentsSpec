# Research: F-USER-002

## Decision 1: Conflict handling

- Decision: email 重複は HTTP 409
- Rationale: クライアントが再試行可否を判定しやすい
- Alternatives considered:
  - 400: 入力不正と区別がつかない

## Decision 2: Error payload format

- Decision: `error_code` と `message` を必須にする
- Rationale: UI 側の分岐処理を安定させる
- Alternatives considered:
  - free text only: 機械可読性が不足
