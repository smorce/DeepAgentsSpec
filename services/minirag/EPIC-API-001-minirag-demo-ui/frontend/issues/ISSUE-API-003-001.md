# Jules AI エージェント向け GitHub Issue テンプレート

> **目的**  
> このテンプレートは、各マイクロサービス実装タスクを GitHub Issue として起票し、Jules AI エージェントに割り当てる際の指示書です。Issue を発行するたびに、下記プレースホルダ(`<...>`)を実際の値に置き換えてください。

---

## 1. 概要
- **サービス名**: `frontend/EPIC-API-001-minirag-demo-ui`
- **対象エピック**: `EPIC-API-001-minirag-demo-ui`
- **対象フィーチャ**: `F-API-003`
- **関連ブランチ**: `F-API-003-minirag-chat-ui`
- **優先度 / 期限**: `High / 2026-01-02`
- **保管場所**: `services/frontend/EPIC-API-001-minirag-demo-ui/issues/ISSUE-API-003-001.md`  
  - *テンプレート記入後は、必ず対象マイクロサービス配下に `issues/` ディレクトリ（無ければ作成）を作り、上記パスへ Markdown ファイルとして保存してください。Pull Request ではこのファイルも含めてください。*

### 期待するユーザー価値
デモ利用者がブラウザ上の静的チャットUIから登録・検索・削除を行い、MiniRAG の検索価値を短時間で理解できる。

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
   - `services/frontend/EPIC-API-001-minirag-demo-ui/service-architecture.md`  
   - `services/frontend/EPIC-API-001-minirag-demo-ui/README.md`  
   - `services/frontend/EPIC-API-001-minirag-demo-ui/service-config.example.yaml`  
   - `services/frontend/EPIC-API-001-minirag-demo-ui/scripts/` 配下の実行スクリプト

4. **エピック / フィーチャ**  
   - ExecPlan: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/exec-plan.md`  
   - Epic design index: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/design/index.md`  
   - Feature Spec: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/spec.md`  
   - Requirements Checklist: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`  
   - PlanQualityGate Checklist: `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md`  
   - 実装計画／補助資料:  
     - `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/impl-plan.md`  
     - `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/research.md`  
     - `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/data-model.md`  
     - `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/contracts/`  
     - `plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/quickstart.md`

5. **ドメイン別チェックリスト（必要に応じて追加）**  
   - 追加が必要な場合のみ `scripts/bash/add-domain-checklist.sh` で生成し、Issue 内にパスと目的を明記する。

---

## 3. プラットフォーム & スタック前提
- **担当レイヤ**: 静的UI（HTML/JS）
- **想定スタック（実装計画準拠）**: HTML/CSS/Vanilla JS（ビルドなし）
- **デモ用途の前提**: 固定デモ API キーを UI に埋め込み、F-API-002 の REST API を呼び出す

---

## 4. 実装ポリシー（必須遵守事項）
1. **仕様駆動 + TDD + Tidy First**  
   - Spec/Plan が不完全な場合は必ず更新し、`scripts/validate_spec.sh` / `scripts/validate_plan.sh` を実行して記録を残すこと。  
   - テストは Red → Green → Refactor の順で追加し、E2E テストコマンドを `scripts/run_all_e2e_tests.sh` に反映する。
2. **決定ログの更新**  
   - 重要な設計判断は対象 ExecPlan の `Decision Log` に追記し、`docs/decisions.md` に要約を追加する。  
   - 進捗は `ExecPlan > Progress` と `harness/AI-Agent-progress.txt` に同時反映する。
3. **サービス境界の尊重**  
   - UI は `services/frontend/EPIC-API-001-minirag-demo-ui/public/` 配下で完結させる。  
   - 外部インターフェースは `contracts/` 配下に残す。
4. **Idempotent な作業手順**  
   - 静的ファイルは差し替え前提で、繰り返し実行しても破壊的にならないこと。  
   - 破壊的操作が必要な場合はバックアップとロールバック方法を Issue 内に明記する。
5. **ガードレール**  
   - `rm -rf`, `git reset --hard`, 機密ファイルアクセスは禁止（AGENTS.md 参照）。

---

## 5. 作業スコープ定義
- **想定アウトプット**  
  - `services/frontend/EPIC-API-001-minirag-demo-ui/public/` 配下の UI 実装  
  - `tests/e2e/scenarios/` の E2E シナリオ  
  - `scripts/run_all_e2e_tests.sh` の更新  
  - 関連ドキュメント（ExecPlan, spec, checklists, contracts 等）の更新
- **除外事項**  
  - なし
- **依存関係 / ブロッカー**  
  - なし

---

## 6. 成功条件 & 検証コマンド
- **動作確認**  
  - `scripts/validate_spec.sh plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/requirements.md`  
  - `scripts/validate_plan.sh plans/services/frontend/EPIC-API-001-minirag-demo-ui/features/F-API-003/checklists/PlanQualityGate.md`  
  - `scripts/run_all_e2e_tests.sh`
- **期待される結果**  
  - validate 系スクリプトは `PASSED` であること。  
  - E2E が `PASS` であること。  
  - UI 操作で「登録→検索→削除」が 3 分以内に完了すること。
  - 空入力時はチャット内に注意メッセージが表示されること。
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
- 検索はチャット入力、登録/削除はボタン操作。
- 結果は上位5件を関連度順で表示。
- エラーはチャット履歴内に表示。

---

> **補足**: Issue 内のすべての記述は、Jules AI エージェントが単独でリポジトリ全体を理解し再開できる水準で具体的に記述してください。文責者は Issue 作成日・氏名を最後に追記することを推奨します。
