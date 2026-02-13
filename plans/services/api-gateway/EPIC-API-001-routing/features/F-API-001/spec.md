# Feature Specification: API Gateway Health Check

**Feature ID**: F-API-001  
**Epic**: EPIC-API-001-ROUTING  
**Status**: Draft  
**Spec Checklist**: `plans/services/api-gateway/EPIC-API-001-routing/features/F-API-001/checklists/requirements.md`

## Overview

API Gateway に最小の監視用エンドポイント `GET /health` を追加し、運用時の生存確認を機械実行可能にする。

## In Scope

- `GET /health` の 200 応答
- 応答ボディに `status` と `service` を含める
- 監視系が再利用できる最小契約を定義

## Out of Scope

- 依存サービスの詳細ヘルスチェック
- DB 接続確認や外部 API 疎通確認

## Functional Requirements

- FR-API-001-001: `GET /health` は HTTP 200 を返すこと
- FR-API-001-002: 応答 JSON は `status="ok"` を含むこと
- FR-API-001-003: 応答 JSON は `service="api-gateway"` を含むこと

## Non-Functional Requirements

- NFR-API-001-001: 応答時間は通常時 800ms 未満
- NFR-API-001-002: ハンドラは副作用を持たない

## References

- `architecture/system-architecture.md`
- `architecture/service-boundaries.md`
- `plans/services/api-gateway/EPIC-API-001-routing/exec-plan.md`

## Success Criteria

- SC-API-001-001: `curl` で 200 を取得できる
- SC-API-001-002: Unit テストでヘルス応答スキーマを検証できる
