# Implementation Plan: F-AVATAR-002

**Branch**: `F-AVATAR-002-profiling` | **Date**: 2026-01-03  
**Epic**: `EPIC-AVATAR-001-diary-minirag` (`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`)  
**Feature Spec**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/spec.md`  
**Spec Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md`  
**Plan Checklist**: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/PlanQualityGate.md` (validate via `scripts/validate_plan.sh`)  

**Input**: Feature specification under  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/spec.md`  
with a passing spec quality checklist at  
`plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md`.

---

## Summary

会話確定後にユーザー発話のみを分析し、固定項目のユーザープロファイルを差分更新する。既存の非空値は空で上書きしない。プロファイリング失敗時は UI に警告表示し、日記登録の成否とは独立に扱う。

---

## Technical Context

**Language/Version**: TypeScript（UI）, Python（server）  
**Primary Services**: avatar-ui（UI + AG-UI server）  
**Primary Dependencies**: Gemini API, YAML プロファイル  
**Storage**: `user_profile.yaml`（固定項目のプロファイル）  
**Testing**: server 側 pytest（プロファイル更新ロジック）, UI は動作確認  
**Target Environment**: ローカル開発（Vite + FastAPI）  
**Project Type**: UI + server の同時変更  
**Constraints**: MiniRAG 登録成功後のみ更新、非空値は空で上書きしない、会話本文はログに出さない

---

## Constitution Check

- **Safety / Security**: OK（本文はログに出さず、プロファイル更新失敗を UI に通知）
- **Maintainability**: OK（プロファイル更新処理は専用モジュールに分離）
- **Complexity / Scope Creep**: OK（会話確定時の更新のみ）
- **Testing / Observability**: OK（差分適用ロジックを単体テスト）

---

## Project Structure

### Documentation (this feature)

text
  plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/
  ├── spec.md
  ├── impl-plan.md
  ├── research.md
  ├── data-model.md
  ├── contracts/
  ├── quickstart.md
  ├── tasks.md
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
  ├── profiling/user_profile.yaml
  ├── profiling/user_profile.default.yaml
  ├── server/main.py
  ├── server/src/diary_service.py
  ├── server/src/profile_service.py (new)
  ├── server/src/profile_store.py (new)
  ├── server/src/config.py
  ├── app/src/renderer/main.ts
  └── app/src/renderer/style.css

**Structure Decision**: プロファイル更新は server 内に専用モジュールを設け、日記確定フローから呼び出す。

---

## Complexity Tracking

該当なし（既存フローへの差分追加）。

---

## Plan of Work

- **Phase 1 – Design**: プロファイル更新データ契約と差分適用ルールを確定する。
- **Phase 2 – Server Implementation**: プロファイル解析/更新モジュールを追加し、日記確定フローに接続する。
- **Phase 3 – UI Integration**: プロファイリング失敗の通知を UI に反映する。
- **Phase 4 – Validation**: 単体テストと手動確認で更新の安全性を検証する。

---

## Concrete Steps

1. データ契約の整備
   - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/contracts/profile-update.schema.json` を追加する。

2. プロファイル更新モジュールを実装
   - `services/avatar-ui/server/src/profile_store.py` に YAML 読み書きロジックを実装する。
   - `services/avatar-ui/server/src/profile_service.py` に以下を実装する。
     - ユーザー発話のみを抽出する整形処理
     - Gemini へのプロファイル差分生成依頼
     - 空上書きを禁止する差分適用ロジック

3. 日記確定フローに統合
   - `services/avatar-ui/server/src/diary_service.py` の日記登録成功後にプロファイル更新を実行する。
   - `/agui/diary/finalize` のレスポンスに profiling ステータスを追加する。

4. UI への通知反映
   - `services/avatar-ui/app/src/renderer/main.ts` で profiling 失敗時の警告メッセージを表示する。
   - 既存の会話確定成功メッセージとは別に失敗通知を出す。

5. 設定更新
   - `services/avatar-ui/server/src/config.py` と `services/avatar-ui/settings.json5` に profiling 設定を追加する（モデル、最低信頼度など）。

6. テスト追加
   - `services/avatar-ui/server/tests/` に差分適用ロジックのユニットテストを追加する。

---

## Validation / Acceptance

- `scripts/validate_spec.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md` → PASSED
- `scripts/validate_plan.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/PlanQualityGate.md` → PASSED
- 手動確認: 会話確定後にプロファイルが更新され、profiling 失敗時は UI に警告表示が出る

---

## Artifacts and Notes

- Epic design index: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`
  - Feature map（F-AVATAR-002）
  - プロファイル更新の差分契約

---

## Idempotence / Recovery

- プロファイル更新が失敗しても日記登録は成功扱いのまま継続できる。
- 失敗時は次回の会話確定で再更新を試みる。
- 既存のプロファイルは空で上書きされないため、繰り返し実行しても情報損失を防げる。

---

## Checklist & Gate Integration

- `checklists/requirements.md` と spec を同期し、`scripts/validate_spec.sh` で確認
- `checklists/PlanQualityGate.md` を維持し、`scripts/validate_plan.sh` の結果を `harness/AI-Agent-progress.txt` に記録
