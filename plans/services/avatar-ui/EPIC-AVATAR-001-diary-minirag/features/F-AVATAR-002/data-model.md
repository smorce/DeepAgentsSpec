# Data Model: F-AVATAR-002

## Entity: UserProfile

**Purpose**: 固定項目のユーザープロファイルを保持する。

**Storage**: YAML（固定キー）

**Rules**:

- 既存の非空値は空で上書きしない
- 更新対象外の項目はそのまま保持する

## Entity: ProfileUpdate

**Purpose**: LLM が生成する差分更新の単位。

**Fields**:

- path (string[], required) — 固定項目の階層パス
- value (string, required) — 更新値（空文字は不可）
- confidence (number, 0-1, required) — 推定の信頼度
- evidence (string, optional) — 推定根拠（短い抜粋）

**Validation Rules**:

- path は固定項目に一致する場合のみ適用
- value が空文字の場合は適用しない
- confidence が閾値未満の場合は適用しない

## Entity: ProfilingStatus

**Purpose**: UI に返す更新結果の状態。

**Fields**:

- status (string, required) — `ok` または `failed`
- message (string, optional) — 失敗時の理由（本文は含めない）
