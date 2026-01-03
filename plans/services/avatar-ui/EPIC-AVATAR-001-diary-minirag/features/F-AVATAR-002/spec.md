# Feature Specification: 日記会話のプロファイリング更新

**Feature ID**: F-AVATAR-002  
**Feature Branch**: `F-AVATAR-002-profiling`  
**Created**: 2026-01-03  
**Status**: Draft  
**Input**: User description: "会話確定時にユーザーの価値観・思考傾向・言葉遣いなどを分析し、固定項目のプロファイルを更新したい"  
**Spec Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md` (validate via `scripts/validate_spec.sh`)

## Overview & Goal *(mandatory)*

日記の会話確定時に、ユーザーの発話内容から価値観・思考傾向・言葉遣いなどを分析し、固定項目のユーザープロファイルを更新できるようにする。既存の非空値は保持し、空欄は空欄のまま維持する。

## Scope & Out of Scope *(mandatory)*

### In Scope

- 会話確定後のプロファイリング更新（ユーザー発話のみを分析対象）
- 既存の非空項目を空で上書きしない更新ルール
- プロファイリング失敗時の UI 通知（本文は表示しない）
- MiniRAG 登録成功後のみプロファイル更新を実行

### Out of Scope

- 複数ユーザーや認証機能
- プロファイル編集 UI の提供
- プロファイルの履歴管理や差分履歴の閲覧
- 会話確定以外のタイミングでの更新

---

## Reference Materials *(mandatory to cite actual docs)*

- `services/avatar-ui/service-architecture.md`
- `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`
- `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`
- `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 会話確定時にプロフィールが更新される (Priority: P1)

利用者は日記会話を確定すると、ユーザー発話の内容に基づいてプロファイルが更新される。

**Why this priority**: プロファイルの更新が主目的であり、会話確定時の自動更新が最重要のため。

**Independent Test**: 会話 → 会話確定 → プロファイルが非空で更新される。

**Acceptance Scenarios**:

1. **Given** ユーザーの発話が含まれる会話履歴がある、**When** 会話確定を行う、**Then** プロファイルの一部項目が更新される
2. **Given** プロファイルに既存の非空値がある、**When** 会話確定を行う、**Then** 既存の非空値は空で上書きされない

---

### User Story 2 - プロファイリング失敗時に通知される (Priority: P1)

利用者はプロファイリングが失敗した場合でも日記登録が成功していることを確認でき、失敗通知が UI に表示される。

**Why this priority**: 失敗時にユーザーが状態を把握できないと不安になるため。

**Independent Test**: プロファイリングの失敗を発生させ、UI に警告表示が出る。

**Acceptance Scenarios**:

1. **Given** 日記登録は成功するがプロファイリングが失敗する、**When** 会話確定を行う、**Then** UI に失敗メッセージが表示される
2. **Given** MiniRAG 登録が失敗する、**When** 会話確定を行う、**Then** プロファイル更新は実行されない

---

### Edge Cases *(mandatory)*

- ユーザー発話が空の場合、プロファイル更新は行われない
- 解析結果が不正形式の場合、プロファイル更新は失敗扱いとなる
- 更新対象外の項目は空欄のまま維持される
- 低信頼度の推定は反映されない

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 会話確定後、MiniRAG 登録が成功した場合のみプロファイル更新を実行しなければならない
- **FR-002**: プロファイル分析はユーザー発話のみを対象としなければならない
- **FR-003**: 既存の非空値は空で上書きしてはならない
- **FR-004**: プロファイリング失敗時は UI に失敗通知を表示しなければならない（本文は表示しない）
- **FR-005**: プロファイル更新対象は固定項目のみとし、更新対象外の項目は保持しなければならない

### Non-Functional Requirements *(include if relevant)*

- **NFR-001**: プロファイリング失敗時のログに会話本文を含めない
- **NFR-002**: 日記登録の成功/失敗とプロファイル更新の成功/失敗を独立に扱う

### Key Entities *(include if feature involves data)*

- **UserProfile**: 固定項目を持つユーザープロファイル
- **ProfileUpdate**: 変更対象のパスと値の集合
- **ProfilingStatus**: 更新結果（成功/失敗と理由）

---

## Assumptions *(mandatory to review; keep short but explicit)*

- 利用者は単一ユーザーであり、プロファイルは単一ファイルに保持される
- プロファイルの項目構造は固定であり、追加・削除は本機能の範囲外

---

## Dependencies & Constraints *(include if relevant)*

- **Dependencies**:
  - Gemini による分析
  - 日記登録フロー（F-AVATAR-001）

- **Constraints**:
  - プロファイル更新は会話確定時のみ実行する
  - MiniRAG 登録が失敗した場合は更新を行わない

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 会話確定後にプロファイルのいずれかの項目が更新される
- **SC-002**: プロファイリング失敗時に UI へ失敗通知が表示される
- **SC-003**: 既存の非空値が空で上書きされない

---

## Checklist & Gate Integration

- Mirror updates from this spec into `checklists/requirements.md` under the same
  feature directory and run `scripts/validate_spec.sh <path-to-requirements.md>`
  until it reports `PASSED`.
- Record spec validation results in `harness/AI-Agent-progress.txt` per project rules.
