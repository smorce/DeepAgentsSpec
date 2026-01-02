# Feature Specification: MiniRAGデモ用チャットUI

**Feature ID**: F-API-003  
**Feature Branch**: `api-003-minirag-ui`  
**Created**: 2026-01-02  
**Status**: Draft  
**Input**: User description: "HTMLベースの簡易チャットUIで、5件の構造化データを登録・削除・検索できるようにする。"  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-003/checklists/requirements.md` (validate via `scripts/validate_spec.sh`)

## Overview & Goal *(mandatory)*

デモ利用者がブラウザ上の簡易チャットUIから、構造化サンプルデータの登録・削除・検索を行えるようにします。  
操作の流れと結果が分かりやすく可視化され、MiniRAGの検索価値を短時間で理解できることがゴールです。

## Scope & Out of Scope *(mandatory)*

### In Scope

- チャット風UIでの検索入力と結果表示
- 5件のサンプルデータを登録する操作
- サンプルデータの削除（個別・一括）
- 操作の成否・現在状態の明確な表示

### Out of Scope

- 複数ユーザー同時利用や認証
- 高度なUIデザインやカスタマイズ機能
- 管理画面や監査ログの提供

---

## Reference Materials *(mandatory to cite actual docs)*

- `architecture/system-architecture.md` → UIとバックエンドの関係性の前提
- `architecture/service-boundaries.md` → UI責務の境界
- `plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md` → 本エピックの作業計画
- `services/avatar-ui/service-architecture.md` → UIサービスの制約
- `temp/MiniRAGのサンプル/minirag_app/docs/MiniRAG_on_postgres.py` → サンプルデータ構造の参考

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 登録→検索の体験 (Priority: P1)

利用者は、UIからサンプルデータを登録し、検索クエリを入力して結果を確認できる。

**Why this priority**: 主要なデモ価値は登録済みデータの検索体験にあるため。

**Independent Test**: 登録ボタン→検索入力→結果表示までを単独で確認できる。

**Acceptance Scenarios**:

1. **Given** 未登録状態、**When** サンプルデータ登録を実行、**Then** 登録完了と現在件数が表示される
2. **Given** 登録済み状態、**When** 検索を実行、**Then** 結果一覧に該当データが表示される

---

### User Story 2 - 削除操作の確認 (Priority: P2)

利用者は、UIから任意のサンプルデータを削除し、結果から消えたことを確認できる。

**Why this priority**: 削除操作の反映が明確でないとデモの信頼性が下がるため。

**Independent Test**: 1件削除→同条件検索→削除対象が表示されないことを確認。

**Acceptance Scenarios**:

1. **Given** 登録済み状態、**When** 任意の1件を削除、**Then** 対象データが結果に表示されない

---

### Edge Cases *(mandatory)*

- 登録前に検索した場合の空結果表示
- 入力が空の場合は検索実行せず、チャット内に注意メッセージを表示する
- バックエンドが一時的に利用不可の場合のエラー表示

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: UIは、チャット風の入力領域と結果表示領域を提供しなければならない
- **FR-002**: UIは、検索クエリをチャット入力で実行できなければならない
- **FR-003**: UIは、5件のサンプルデータを一括登録するボタン操作を提供しなければならない
- **FR-004**: UIは、サンプルデータの個別削除および一括削除のボタン操作を提供しなければならない
- **FR-005**: UIは、検索結果の上位5件を関連度降順で一覧表示し、タイトル・要約・主要属性が確認できなければならない
- **FR-006**: UIは、登録・削除・検索の成功/失敗をユーザーに分かる形で表示しなければならない
- **FR-007**: UIは、エラー発生時にチャット履歴内へエラーメッセージを表示しなければならない

### Non-Functional Requirements *(include if relevant)*

- **NFR-001**: UIは一般的なデスクトップとスマートフォン画面で主要操作が完了できる
- **NFR-002**: 操作結果はユーザーが直感的に理解できる表現で表示される
- **NFR-003**: 入力が空の場合は検索実行せず、チャット内に注意メッセージを表示する

### Key Entities *(include if feature involves data)*

- **SampleStructuredRecord**: doc_id, title, summary, body, status, region, priority, created_at, metadata を含む表示対象データ
- **ChatMessage**: role, content, timestamp を持つUI表示メッセージ

---

## Assumptions *(mandatory to review; keep short but explicit)*

- UIはデモ用途であり、単一ユーザーの操作を前提とする
- 操作はバックエンド（F-API-002）の提供する機能に依存する
- サンプルデータは固定の5件で運用する

---

## Dependencies & Constraints *(include if relevant)*

- **Dependencies**:
  - F-API-002（MiniRAGバックエンド機能）

- **Constraints**:
  - UIはブラウザで動作する簡易チャットUIであること
  - デモ利用を想定した最小限の画面構成とすること
  - UIは固定のデモ用APIキーを使用してバックエンド要求を行うこと

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 初めて利用する人の90%が、3分以内に登録→検索→削除の一連操作を完了できる
- **SC-002**: 主要操作（登録・検索・削除）の結果が全て画面上で明確に確認できる
- **SC-003**: 失敗時にユーザーが次の行動を理解できるメッセージが表示される

---

## Checklist & Gate Integration

- Mirror updates from this spec into `checklists/requirements.md` under the same
  feature directory and run `scripts/validate_spec.sh <path-to-requirements.md>`
  until it reports `PASSED`.
- If additional domain checklists are generated via `scripts/*/add-domain-checklist.*`,
  reference them in this spec where relevant (e.g., Security requirements).
- Record spec validation results in `harness/AI-Agent-progress.txt` per project rules.
