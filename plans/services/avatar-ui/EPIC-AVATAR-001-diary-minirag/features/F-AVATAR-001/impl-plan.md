# Implementation Plan: F-AVATAR-001

**Branch**: `F-AVATAR-001-diary-minirag` | **Date**: 2026-01-03  
**Epic**: `EPIC-AVATAR-001-diary-minirag` (`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`)  
**Feature Spec**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`  
**Spec Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md`  
**Plan Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/PlanQualityGate.md` (validate via `scripts/validate_plan.sh`)  

**Input**: Feature specification under  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`  
with a passing spec quality checklist at  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md`.

---

## Summary

avatar-ui に「会話確定」と「検索トグル」を追加し、Gemini 会話を日記として構造化して MiniRAG に登録する。検索は Gemini のツール呼び出しで自律的に行い、doc_id / summary / body の上位N件のみを文脈として渡す。UI はトグルと top_k を提供し、ユーザーが検索利用を制御できる。

---

## Technical Context

**Language/Version**: TypeScript（UI）, Python（server）  
**Primary Services**: avatar-ui（UI + AG-UI server）  
**Primary Dependencies**: MiniRAG API（`POST /minirag/documents/bulk`, `POST /minirag/search`）  
**Storage**: MiniRAG（外部）; avatar-ui は一時メモリのみ  
**Testing**: server 側の pytest、必要なら UI のスモーク確認  
**Target Environment**: ローカル開発（Vite + FastAPI）  
**Project Type**: UI + server の同時変更  
**Performance Goals**: 日記確定操作がユーザーにとって待てる時間内（数十秒以内）  
**Constraints**: workspace 固定 `diary`、検索トグル OFF 時は検索禁止、MiniRAG API は変更しない

---

## Constitution Check

- **Safety / Security**: OK（外部 API キーは `.env` 管理、ログに本文を残さない）
- **Maintainability**: OK（設定は `settings.json5` と config に集約）
- **Complexity / Scope Creep**: OK（avatar-ui 内で完結）
- **Testing / Observability**: OK（server の単体テストと簡易動作確認）

---

## Project Structure

### Documentation (this feature)

text
  plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/
  ├── spec.md
  ├── impl-plan.md
  ├── research.md
  ├── data-model.md
  ├── quickstart.md
  ├── contracts/
  └── checklists/
      ├── requirements.md
      └── PlanQualityGate.md

### Epic-level Design (cross-feature context)

text
  plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/
  ├── exec-plan.md
  └── design/
      └── index.md

### Source Code (repository root)

text
  services/avatar-ui/
  ├── app/src/renderer/index.html
  ├── app/src/renderer/main.ts
  ├── app/src/renderer/style.css
  ├── server/main.py
  ├── server/src/config.py
  ├── server/src/minirag_client.py (new)
  ├── server/src/diary_service.py (new)
  └── server/src/routes/diary.py (new)

**Structure Decision**: UI は既存の renderer にボタンとトグルを追加し、サーバーは新規モジュールで MiniRAG 連携と日記解析フローを分離する。

---

## Complexity Tracking

該当なし（新規 API と UI 追加のみ）。

---

## Plan of Work

- **Phase 1 – Server Design**: MiniRAG クライアント、日記解析サービス、検索ツールを分離して設計する。
- **Phase 2 – UI Design**: 検索トグル、top_k 入力、会話確定ボタンとトランスクリプト収集を追加する。
- **Phase 3 – Integration**: UI → server の API をつなぎ、Gemini ツールに検索コンテキストを渡す。
- **Phase 4 – Validation**: pytest と手動の動作確認で主要フローを検証する。

---

## Concrete Steps

1. サーバー側の MiniRAG クライアントを追加する
   - `services/avatar-ui/server/src/minirag_client.py` に `bulk_insert` と `search` を実装する。

2. 日記解析サービスを追加する
   - `services/avatar-ui/server/src/diary_service.py` に Gemini 解析プロンプトと JSON 解析を実装する。

3. 新規 API ルートを追加する
   - `services/avatar-ui/server/src/routes/diary.py` に `/agui/diary/finalize` と `/agui/diary/search-settings` を定義する。
   - `services/avatar-ui/server/main.py` にルート登録とツール追加を行う。

4. 設定を追加する
   - `services/avatar-ui/server/src/config.py` に MiniRAG の base_url / workspace / top_k を追加し、`settings.json5` から読み込む。

5. UI を更新する
   - `services/avatar-ui/app/src/renderer/index.html` にトグル・top_k・確定ボタンを追加する。
   - `services/avatar-ui/app/src/renderer/main.ts` でトランスクリプト収集と API 呼び出しを実装する。
   - `services/avatar-ui/app/src/renderer/style.css` で UI コンポーネントのスタイルを追加する。

6. テストを追加する
   - `services/avatar-ui/server/tests/` に diary API のユニットテストを追加する。

---

## Validation / Acceptance

- `scripts/validate_spec.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md` → PASSED
- `scripts/validate_plan.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/PlanQualityGate.md` → PASSED
- 手動確認: UI で会話確定ボタンを押すと MiniRAG 登録が成功し、検索トグル OFF 時には検索が行われない

---

## Artifacts and Notes

- Epic design index: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`
  - Feature map, shared entities, cross-feature flows

---

## Idempotence / Recovery

- 追加 API が失敗した場合は UI から再試行できる。
- 設定追加に失敗した場合は `settings.json5` を元に戻すことで復旧できる。
- MiniRAG 登録が失敗した場合は同じ会話を再度確定できる。

---

## Checklist & Gate Integration

- `checklists/requirements.md` と spec を同期し、`scripts/validate_spec.sh` で確認
- `checklists/PlanQualityGate.md` を維持し、`scripts/validate_plan.sh` の結果を `harness/AI-Agent-progress.txt` に記録

