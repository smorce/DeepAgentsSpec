# Jules AI エージェント向け GitHub Issue テンプレート

> **目的**  
> このテンプレートは、各マイクロサービス実装タスクを GitHub Issue として起票し、Jules AI エージェントに割り当てる際の指示書です。Issue を発行するたびに、下記プレースホルダ(`<...>`)を実際の値に置き換えてください。

---

## 1. 概要
- **サービス名**: `avatar-ui`
- **対象エピック**: `EPIC-AVATAR-001-DIARY-MINIRAG`
- **対象フィーチャ**: `F-AVATAR-001`
- **関連ブランチ**: `TBD (推奨: F-AVATAR-001-diary-minirag)`
- **優先度 / 期限**: `P1 / TBD`
- **保管場所**: `services/avatar-ui/issues/ISSUE-AVATAR-001-001.md`  
  - *テンプレート記入後は、必ず対象マイクロサービス配下に `issues/` ディレクトリ（無ければ作成）を作り、上記パスへ Markdown ファイルとして保存してください。Pull Request ではこのファイルも含めてください。*

### 期待するユーザー価値
Gemini との日記会話をユーザーが明示的に確定し、重要度・サマリー・記憶を構造化したうえで MiniRAG に保存できる。過去日記の文脈を Gemini が必要時に参照できる。

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
   - Feature Spec: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/spec.md`  
   - Requirements Checklist: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md`  
   - PlanQualityGate Checklist: `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/PlanQualityGate.md`  
   - 実装計画／補助資料:  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/impl-plan.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/research.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/data-model.md`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/contracts/`  
     - `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/quickstart.md`

5. **ドメイン別チェックリスト（必要に応じて追加）**  
   - 追加観点が必要なら `scripts/bash/add-domain-checklist.sh` で作成し、Issue 内にパスを明記する。

---

## 3. プラットフォーム & スタック前提

avatar-ui はローカル UI + ローカル AG-UI サーバーの構成であり、記載の Next.js / Workers / Neon / Supabase / Stripe とは直接関係しない。  
ただし外部 API 呼び出し（MiniRAG）を含むため、I/O の失敗を明確に扱い、再試行・エラーメッセージを UI に返せる設計を維持する。

---

## 4. 実装ポリシー（必須遵守事項）
1. **仕様駆動 + TDD + Tidy First**  
   - Spec/Plan の更新が発生した場合は `scripts/validate_spec.sh` / `scripts/validate_plan.sh` を実行して記録する。  
   - テストは必須ではないが、追加する場合は Red → Green → Refactor を守る。
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
  - `services/avatar-ui/server/src/` の MiniRAG 連携・日記確定 API 追加  
  - `services/avatar-ui/app/src/renderer/` の UI 改修（検索トグル / top_k / 会話確定）  
  - `services/avatar-ui/settings.json5` / `services/avatar-ui/server/src/config.py` の設定拡張  
  - 仕様に応じたドキュメント更新
- **除外事項**  
  - MiniRAG API 側（api-gateway）の修正  
  - 認証・ユーザー管理  
  - 日記の編集・削除・公開
- **依存関係 / ブロッカー**  
  - MiniRAG API が稼働していること（`/minirag/documents/bulk`, `/minirag/search`）  
  - Gemini API キーなどの `.env` 設定

---

## 6. 成功条件 & 検証コマンド
- **動作確認**  
  - `scripts/validate_spec.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/requirements.md`  
  - `scripts/validate_plan.sh plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/checklists/PlanQualityGate.md`
- **期待される結果**  
  - Spec/Plan の品質ゲートが PASSED となる。
  - UI の「会話確定」ボタンで MiniRAG 登録が成功し、重要度とサマリーが UI に表示される。
  - 検索トグル ON のときのみ MiniRAG 検索が実行される。
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
- 実装タスクは `plans/services/avatar-ui/EPIC-AVATAR-001-diary-minirag/features/F-AVATAR-001/tasks.md` を唯一の source of truth とする。
- workspace は固定値 `diary` を使用する。

---

> 補足: 本 Issue は 2026-01-03 に codex が作成。
