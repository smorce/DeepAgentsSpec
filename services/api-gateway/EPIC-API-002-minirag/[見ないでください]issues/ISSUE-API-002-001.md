# Jules AI エージェント向け GitHub Issue テンプレート

> **目的**  
> このテンプレートは、各マイクロサービス実装タスクを GitHub Issue として起票し、Jules AI エージェントに割り当てる際の指示書です。Issue を発行するたびに、下記プレースホルダ(`<...>`)を実際の値に置き換えてください。

---

## 1. 概要
- **サービス名**: `api-gateway`
- **対象エピック**: `EPIC-API-002-minirag`
- **対象フィーチャ**: `F-API-002`
- **関連ブランチ**: `F-API-002-minirag-backend`
- **優先度 / 期限**: `High / 2026-01-02`
- **保管場所**: `services/api-gateway/issues/ISSUE-API-002-001.md`  
  - *テンプレート記入後は、必ず対象マイクロサービス配下に `issues/` ディレクトリ（無ければ作成）を作り、上記パスへ Markdown ファイルとして保存してください。Pull Request ではこのファイルも含めてください。*

### 期待するユーザー価値
デモ利用者が構造化サンプルデータを「登録→検索→削除」でき、検索結果の妥当性と削除反映を短時間で確認できる。

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
   - `services/api-gateway/service-architecture.md`  
   - `services/api-gateway/README.md`  
   - `services/api-gateway/service-config.example.yaml`  
   - `services/api-gateway/scripts/` 配下のテスト実行スクリプト

4. **エピック / フィーチャ**  
   - ExecPlan: `plans/services/api-gateway/EPIC-API-002-minirag/exec-plan.md`  
   - Epic design index: （本ブランチでは未作成）  
   - Feature Spec: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/spec.md`  
   - Requirements Checklist: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`  
   - PlanQualityGate Checklist: `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md`  
   - 実装計画／補助資料:  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/impl-plan.md`  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/research.md`  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/data-model.md`  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/contracts/`  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/quickstart.md`  
     - `plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/tasks.md`

5. **ドメイン別チェックリスト（必要に応じて追加）**  
   - 追加が必要な場合のみ `scripts/bash/add-domain-checklist.sh` で生成し、Issue 内にパスと目的を明記する。

---

## 3. プラットフォーム & スタック前提
- **担当レイヤ**: API Gateway（HTTP API）
- **想定スタック（実装計画準拠）**: Python / FastAPI / PostgreSQL(pgvector) / MiniRAG
- **デモ用途の前提**: ローカル環境で再現可能な起動手順、固定デモ API キー必須

---

## 4. 実装ポリシー（必須遵守事項）
1. **仕様駆動 + TDD + Tidy First**  
   - Spec/Plan が不完全な場合は必ず更新し、`scripts/validate_spec.sh` / `scripts/validate_plan.sh` を実行して記録を残すこと。  
   - テストは Red → Green → Refactor の順で追加し、ユニット・統合・E2E 各層の想定テストコマンドを `scripts/run_all_*.sh` に反映する。
2. **決定ログの更新**  
   - 重要な設計判断は対象 ExecPlan の `Decision Log` に追記し、`docs/decisions.md` に要約を追加する。  
   - 進捗は `ExecPlan > Progress` と `harness/AI-Agent-progress.txt` に同時反映する。
3. **サービス境界の尊重**  
   - API Gateway / User Service / Billing Service が触れるデータ・API は `architecture/service-boundaries.md` に従い、責務を越境しない。  
   - 外部インターフェースは `contracts/` 配下にヘッダ・スキーマを残す。
4. **Idempotent な作業手順**  
   - 初期化・テストスクリプトは複数回実行しても破壊的にならないこと。  
   - 破壊的操作が必要な場合はバックアップとロールバック方法を Issue 内に明記する。
5. **ガードレール**  
   - `rm -rf`, `git reset --hard`, 機密ファイルアクセスは禁止（AGENTS.md 参照）。

---

## 5. 作業スコープ定義
- **想定アウトプット**  
  - `services/api-gateway/src/` 配下の実装コード  
  - `services/api-gateway/tests/` のテストケース  
  - `tests/e2e/scenarios/` の E2E シナリオ  
  - `scripts/run_all_unit_tests.sh`, `scripts/run_all_e2e_tests.sh` の更新  
  - 関連ドキュメント（ExecPlan, spec, checklists, contracts 等）の更新
- **除外事項**  
  - なし
- **依存関係 / ブロッカー**  
  - なし

---

## 6. 成功条件 & 検証コマンド
- **動作確認**  
  - `scripts/validate_spec.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/requirements.md`  
  - `scripts/validate_plan.sh plans/services/api-gateway/EPIC-API-002-minirag/features/F-API-002/checklists/PlanQualityGate.md`  
  - `scripts/run_all_unit_tests.sh`  
  - `scripts/run_all_e2e_tests.sh`  
  - `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/documents/bulk ...`  
  - `curl -H "X-Demo-Api-Key: <key>" -X POST http://localhost:8000/minirag/search ...`
- **期待される結果**  
  - validate 系スクリプトは `PASSED` であること。  
  - Unit/E2E が全て `PASS` であること。  
  - 登録/検索/削除の API が 200 を返し、検索 0 件時は空配列＋注記が返ること。
- **Checklists**  
  - `requirements.md` / `PlanQualityGate.md` を完了し、結果を Issue 本文に記載。
- **ログ提出**  
  - 実行コマンドと結果を Issue コメントに要約し、ExecPlan の Validation セクションにも反映。

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
- 登録は Upsert、削除は件数返却、0件検索は空配列＋注記。
- API キーは `X-Demo-Api-Key` を必須とする。

---

> **補足**: Issue 内のすべての記述は、Jules AI エージェントが単独でリポジトリ全体を理解し再開できる水準で具体的に記述してください。文責者は Issue 作成日・氏名を最後に追記することを推奨します。
