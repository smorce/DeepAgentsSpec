# Research: F-USER-001

## Decision 1: Validation timing

- Decision: 入力時 + 送信時の二段階で検証
- Rationale: UX と不正入力抑止を両立できる
- Alternatives considered:
  - 送信時のみ検証: フィードバックが遅い

## Decision 2: Error rendering

- Decision: フォーム下部にインライン表示
- Rationale: ユーザーが修正しやすい
- Alternatives considered:
  - モーダル表示: 操作を中断しやすい
