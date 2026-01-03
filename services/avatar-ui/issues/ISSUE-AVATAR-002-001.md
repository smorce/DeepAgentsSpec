# Jules AI エージェント向け GitHub Issue テンプレート

> **目的**  
> このテンプレートは、各マイクロサービス実装タスクを GitHub Issue として起票し、Jules AI エージェントに割り当てる際の指示書です。Issue を発行するたびに、下記プレースホルダ(`<...>`)を実際の値に置き換えてください。

---

## 1. 概要
- **サービス名**: `avatar-ui`
- **対象エピック**: `EPIC-AVATAR-001-DIARY-MINIRAG`
- **対象フィーチャ**: `F-AVATAR-002`
- **関連ブランチ**: `TBD (推奨: F-AVATAR-002-profiling)`
- **優先度 / 期限**: `P1 / TBD`
- **保管場所**: `services/avatar-ui/issues/ISSUE-AVATAR-002-001.md`  
  - *テンプレート記入後は、必ず対象マイクロサービス配下に `issues/` ディレクトリ（無ければ作成）を作り、上記パスへ Markdown ファイルとして保存してください。Pull Request ではこのファイルも含めてください。*

### 期待するユーザー価値
会話確定時にユーザーの価値観・思考傾向・言葉遣いなどが自動でプロフィールへ反映され、失敗時も UI で状態を把握できる。

---

## 2. 参照すべき設計アーティファクト
AI エージェントは以下の順序でドキュメントを読んでください。必要に応じて Issue 発行時に特記事項を追記します。

1. **システム全体**  
   - `architecture/system-architecture.md`  
   - `architecture/service-boundaries.md`  
   - `architecture/deployment-topology.md`  
   - 図版: `architecture/diagrams/`

2. **ハーネス & ルール**  
   - `README.md`（リポジトリ全体のコンセプト）  
   - `docs/onboarding.md`（作業フロー）  
   - `PLANS.md`（ExecPlan 作成・更新ルール）  
   - `harness/feature_list.json`（対象エピック/フィーチャの真実のソース）  
   - `harness/AI-Agent-progress.txt`（進捗ログの追記ルール）  
   - `harness/harness-config.yaml`（スクリプト参照先）

3. **サービス固有**  
   - `services/avatar-ui/service-architecture.md`  
   - `services/avatar-ui/README.ja.md`  
   - `services/avatar-ui/service-config.example.yaml`  
   - `services/avatar-ui/scripts/` 配下のテスト実行スクリプト

4. **エピック / フィーチャ**  
   - ExecPlan: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/exec-plan.md`  
   - Epic design index: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/design/index.md`  
   - Feature Spec: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/spec.md`  
   - Requirements Checklist: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md`  
   - PlanQualityGate Checklist: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/PlanQualityGate.md`  
   - 実装計画／補助資料:  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/impl-plan.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/research.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/data-model.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/contracts/`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/quickstart.md`

5. **ドメイン別チェックリスト（必要に応じて追加）**  
   - 追加観点が必要なら `scripts/bash/add-domain-checklist.sh` で作成し、Issue 内にパスを明記する。

---

## 3. プラットフォーム & スタック前提

avatar-ui はローカル UI + ローカル AG-UI サーバーの構成であり、Next.js / Workers / Neon / Supabase / Stripe とは直接関係しない。  
ただし将来の移行を阻害しないよう、I/O 失敗時の扱いとエラーメッセージの明確化を維持する。

---

## 4. 実装ポリシー（必須遵守事項）
1. **仕様駆動 + TDD + Tidy First**  
   - Spec/Plan の更新が発生した場合は `scripts/validate_spec.sh` / `scripts/validate_plan.sh` を実行して記録する。  
   - テストは Red → Green → Refactor の順で追加する。
2. **決定ログの更新**  
   - 重要な設計判断は ExecPlan の `Decision Log` と `docs/decisions.md` に追記する。  
   - 進捗は `ExecPlan > Progress` と `harness/AI-Agent-progress.txt` に反映する。
3. **サービス境界の尊重**  
   - MiniRAG API の仕様変更は行わない（呼び出しのみ）。  
   - avatar-ui 内で完結する実装に限定する。
4. **Idempotent な作業手順**  
   - 失敗時は再実行で復旧できるようにする。
5. **ガードレール**  
   - `rm -rf`, `git reset --hard`, 機密ファイルアクセスは禁止（AGENTS.md 参照）。

---

## 5. 作業スコープ定義
- **想定アウトプット**  
  - `services/avatar-ui/server/src/profile_store.py` / `profile_service.py` の新設  
  - `services/avatar-ui/server/src/diary_service.py` / `routes/diary.py` の profiling 統合  
  - `services/avatar-ui/app/src/renderer/main.ts` の UI 警告表示追加  
  - `services/avatar-ui/profiling/user_profile.yaml` の差分更新ロジック  
  - `services/avatar-ui/server/src/config.py` / `services/avatar-ui/settings.json5` の profiling 設定追加  
  - 仕様に応じたドキュメント更新
- **除外事項**  
  - プロファイル編集 UI の追加  
  - 複数ユーザー対応や認証  
  - MiniRAG API 側の修正
- **依存関係 / ブロッカー**  
  - MiniRAG 登録が成功していること（profiling は登録成功後のみ実行）  
  - Gemini API キー等の `.env` 設定

---

## 6. 成功条件 & 検証コマンド
- **動作確認**  
  - `scripts/validate_spec.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/requirements.md`  
  - `scripts/validate_plan.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/checklists/PlanQualityGate.md`
- **期待される結果**  
  - Spec/Plan の品質ゲートが PASSED となる。  
  - 会話確定後にプロファイルが更新される。  
  - profiling 失敗時は UI に警告が表示される（本文は表示しない）。  
  - 既存の非空値が空で上書きされない。
- **Checklists**  
  - `requirements.md` / `PlanQualityGate.md` が完了済みであること。
- **ログ提出**  
  - 実行コマンドと要約結果を Issue コメントで報告し、ExecPlan の Validation に反映する。

---

## 7. ハンドオフ / Close 条件チェックリスト
- [ ] Feature Spec と Requirements checklist が最新かつ `validate_spec.sh` PASSED  
- [ ] PlanQualityGate checklist が更新済みで `validate_plan.sh` PASSED  
- [ ] ソースコード・テスト・スクリプト・ドキュメントがコミットされている  
- [ ] `harness/feature_list.json` の対象 Feature `status` を最新化  
- [ ] `harness/AI-Agent-progress.txt` にセッション結果を追記  
- [ ] Issue コメントに検証ログ・主要決定を要約  
- [ ] Pull Request には単一行メッセージで要約（Git ルール参照）

---

## 8. 追加メモ
- 実装タスクは `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-002/tasks.md` を唯一の source of truth とする。  
- プロファイル更新は差分方式で、空値で既存の非空値を上書きしない。  
- プロファイリング失敗時は WARN ログ（本文は出さない）＋ UI 警告を必須とする。

---

> 補足: 本 Issue は 2026-01-03 に codex が作成。
