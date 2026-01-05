# Epic Design Index: EPIC-API-001-MINIRAG-DEMO-UI

## 1. Scope & Owner

- ExecPlan: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/exec-plan.md`
- Scope:
  - Service: frontend/EPIC-API-001-minirag-demo-ui
  - Primary services: frontend/EPIC-API-001-minirag-demo-ui, api-gateway
- Summary:
  - 静的UIで MiniRAG デモの登録・検索・削除体験を成立させる。

---

## 2. Feature Map

| Feature ID | Title | Spec Path | Impl Plan | Data Model | Contracts Dir | Quickstart |
| --- | --- | --- | --- | --- | --- | --- |
| F-API-003 | MiniRAGデモ用チャットUI | `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md` | `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/impl-plan.md` | `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/data-model.md` | `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/contracts/` | `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/quickstart.md` |

---

## 3. Shared Entities & Ownership

| Entity | Owning Feature ID | Services involved | Notes |
| --- | --- | --- | --- |
| StructuredDocument | F-API-002（外部） | api-gateway, frontend | UI は表示のみを担当 |
| SearchResult | F-API-002（外部） | api-gateway, frontend | UI 表示用の検索結果 |

---

## 4. Shared APIs / Contracts

| Contract / Endpoint | Owner Feature | Path / Topic | Consumers | Notes |
| --- | --- | --- | --- | --- |
| Search API | F-API-002（外部） | `POST /minirag/search` | F-API-003 | 上位5件を返す |
| Register API | F-API-002（外部） | `POST /minirag/documents/bulk` | F-API-003 | 5件一括登録 |
| Delete API (single) | F-API-002（外部） | `DELETE /minirag/documents/{doc_id}` | F-API-003 | 削除件数を返す |
| Delete API (all) | F-API-002（外部） | `DELETE /minirag/documents` | F-API-003 | 全件削除 |

---

## 5. Cross-Feature Flows

### 登録→検索→削除フロー
1. F-API-003 UI から登録操作
2. F-API-002 が5件を登録
3. UI から検索クエリを送信
4. F-API-002 が検索結果を返却
5. UI から削除（個別/一括）を送信
