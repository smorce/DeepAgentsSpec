# Feature Specification: MiniRAG構造化データ登録・検索バックエンド

**Feature ID**: F-API-002  
**Feature Branch**: `api-002-minirag-backend`  
**Created**: 2026-01-02  
**Status**: Draft  
**Input**: User description: "MiniRAG をマイクロサービスとして取り込み、構造化データを登録・検索・削除できるようにする。"  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md` (validate via `scripts/validate_spec.sh`)

## Overview & Goal *(mandatory)*

MiniRAGを利用した構造化データの登録・検索・削除をバックエンドで提供し、サンプルデータを使った検索体験を成立させます。  
デモ利用者が、登録→検索→削除までの一連操作を確実に実行できることを目的とします。

## Scope & Out of Scope *(mandatory)*

### In Scope

- 5件の構造化サンプルデータを登録できること
- サンプルデータを検索し、関連する結果を返せること
- サンプルデータを削除できること（個別・一括）
- 登録・検索・削除の成否をユーザーに明確に返すこと

### Out of Scope

- 企業本番運用向けの大規模データ管理
- 高度な権限管理やユーザー認証
- 学習データの自動収集や外部ソース取り込み

---

## Reference Materials *(mandatory to cite actual docs)*

- `architecture/system-architecture.md` → システム全体の役割分担とハーネス前提
- `architecture/service-boundaries.md` → バックエンドとUIの責務境界
- `plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md` → 本エピックの作業計画
- `services/api-gateway/service-architecture.md` → api-gatewayの制約とI/F方針
- `temp/MiniRAGのサンプル/minirag_app/docs/MiniRAG_on_postgres.py` → 構造化データ登録・検索の参考実装

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - サンプルデータの一括登録と検索 (Priority: P1)

デモ利用者は、5件の構造化データを一括登録し、検索クエリで該当する結果を確認できる。

**Why this priority**: 主要価値は「登録したデータを検索できる」ことにあるため。

**Independent Test**: 5件を登録→任意の検索クエリを実行→検索結果に該当データが含まれることを確認。

**Acceptance Scenarios**:

1. **Given** 未登録状態、**When** サンプルデータを一括登録する、**Then** 5件すべてが登録済みとして確認できる
2. **Given** 登録済み状態、**When** 関連する検索クエリを実行する、**Then** 上位結果に該当データが返る

---

### User Story 2 - データ削除と検索結果反映 (Priority: P2)

利用者は、任意のサンプルデータを削除し、検索結果から消えることを確認できる。

**Why this priority**: デモの信頼性には削除操作と反映の明確さが必要なため。

**Independent Test**: 1件削除→同条件で検索→削除対象が結果に含まれないことを確認。

**Acceptance Scenarios**:

1. **Given** 登録済み状態、**When** 任意の1件を削除する、**Then** そのデータが検索結果に出現しない

---

### Edge Cases *(mandatory)*

- 検索クエリが空または無関係で結果が0件の場合は正常扱いとし、空配列と「0件」である旨の注記を返す
- 既に登録済みの同一データ（同一 doc_id）を再登録した場合は上書き（Upsert）する
- 依存サービスが一時的に利用不可の場合のエラーハンドリング

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、5件の構造化サンプルデータを一括登録できなければならない
- **FR-002**: システムは、サンプルデータを個別および一括で削除できなければならない
- **FR-003**: システムは、検索クエリに対して関連するサンプルデータを順位付きで返さなければならない
- **FR-004**: システムは、登録データが再起動後も利用可能であることを保証しなければならない
- **FR-005**: システムは、登録・削除・検索の成功/失敗を利用者に明確に返さなければならない
- **FR-006**: システムは、同一 doc_id の登録要求に対して既存データを上書き（Upsert）しなければならない
- **FR-007**: システムは、検索結果が0件のとき空配列と「0件」である旨の注記を返さなければならない
- **FR-008**: システムは、削除時に削除件数（0件含む）を返さなければならない

### Non-Functional Requirements *(include if relevant)*

- **NFR-001**: 通常利用時、利用者は検索結果を3秒以内に確認できる
- **NFR-002**: 依存サービス障害時、利用者に理解可能なエラーメッセージが提示される
- **NFR-003**: 本APIは固定のデモ用APIキーによる認可を必須とする

### Key Entities *(include if feature involves data)*

- **StructuredDocument**: workspace, doc_id, title, summary, body, status, region, priority, created_at, metadata を持つ構造化ドキュメント（workspace + doc_id で一意）
- **SearchResult**: doc_id, title, summary, relevance, source_fields を含む検索結果

---

## Assumptions *(mandatory to review; keep short but explicit)*

- 本機能はデモ用途を主目的とし、同時多数ユーザーの利用は想定しない
- 5件のサンプルデータは事前に定義された固定セットである
- UI側は本バックエンドの操作結果をそのまま表示する

---

## Dependencies & Constraints *(include if relevant)*

- **Dependencies**:
  - MiniRAGサービスの利用
  - UI機能（F-API-003）からの操作呼び出し

- **Constraints**:
  - 構造化データの永続化はリレーショナルDBを用いる
  - 応答生成には `deepseek/deepseek-v3.2-speciale` を用いる
  - ローカル環境で再現可能な起動手順があること

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 利用者が5件のサンプル登録を1分以内に完了できる
- **SC-002**: 関連クエリの90%で、上位3件に該当結果が含まれる
- **SC-003**: 1件削除後、5秒以内に検索結果から消える
- **SC-004**: 再起動後も登録済みデータが100%維持される

---

## Checklist & Gate Integration

- Mirror updates from this spec into `checklists/requirements.md` under the same
  feature directory and run `scripts/validate_spec.sh <path-to-requirements.md>`
  until it reports `PASSED`.
- If additional domain checklists are generated via `scripts/*/add-domain-checklist.*`,
  reference them in this spec where relevant (e.g., Security requirements).
- Record spec validation results in `harness/AI-Agent-progress.txt` per project rules.
