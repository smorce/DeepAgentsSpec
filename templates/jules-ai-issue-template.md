# Jules AI エージェント向け GitHub Issue テンプレート

> **目的**  
> このテンプレートは、各マイクロサービス実装タスクを GitHub Issue として起票し、Jules AI エージェントに割り当てる際の指示書です。Issue を発行するたびに、下記プレースホルダ(`<...>`)を実際の値に置き換えてください。

---

## 1. 概要
- **サービス名**: `<service-name>`
- **対象エピック**: `<EPIC-ID (例: EPIC-API-001-ROUTING)>`
- **対象フィーチャ**: `<FEATURE-ID (例: F-API-001)>`
- **関連ブランチ**: `<feature-branch or TBD>`
- **優先度 / 期限**: `<priority / due-date>`
- **保管場所**: `services/<service-name>/issues/<issue-id>.md`  
  - *テンプレート記入後は、必ず対象マイクロサービス配下に `issues/` ディレクトリ（無ければ作成）を作り、上記パスへ Markdown ファイルとして保存してください。Pull Request ではこのファイルも含めてください。*

### 期待するユーザー価値
`<このサービス実装でユーザーが得る価値を1〜2文で記述>`

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
   - `services/<service-name>/service-architecture.md`  
   - `services/<service-name>/README.md`  
   - `services/<service-name>/service-config.example.yaml`  
   - `services/<service-name>/scripts/` 配下のテスト実行スクリプト

4. **エピック / フィーチャ**  
   - ExecPlan: `plans/services/<service-name>/<EPIC-ID>/exec-plan.md`（または system スコープの場合は `plans/system/<EPIC-ID>/exec-plan.md`）  
   - Epic design index: `plans/<scope>/<service-name>/<EPIC-ID>/design/index.md`（存在する場合）  
   - Feature Spec: `plans/<scope>/<service-name>/<EPIC-ID>/features/<FEATURE-ID>/spec.md`  
   - Requirements Checklist: `.../checklists/requirements.md`  
   - PlanQualityGate Checklist: `.../checklists/PlanQualityGate.md`  
   - 実装計画／補助資料（存在する場合）: `impl-plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

---

## 3. プラットフォーム & スタック前提
> **基本方針**: MVP 段階はローカル開発（個人利用）を前提に進める。ただし各 Issue では、以下の本番スタックに移行可能な設計を常に意識すること。

- **アプリ層**: Next.js (SSR)  
  - OpenNext 経由で Cloudflare Workers へデプロイする。  
  - API Routes / Middleware を活用し、エッジでの低遅延実行を最優先。  
  - `wrangler.jsonc` では `minify: true` を設定し、アセット（gzip）を最小化する。
- **データベース**: Neon (サーバーレス PostgreSQL)  
- **認証/認可**: Supabase Auth  
  - JWT ベースセッション、Row Level Security を全テーブルで有効化（原則 `user_id = auth.uid()` 条件）。  
  - CHECK 制約を積極活用して不正データを遮断する。
- **ストレージ / CDN**:  
  - Cloudflare R2（S3 互換 API）にユーザーアップロードを保存。Workers 経由で直接 PUT すること。  
  - Cloudflare Images は R2 をソースにリサイズ・最適化を実行し、配信を担当。  
  - 無料枠を活用するため、Images はオンザフライ処理に限定。
- **決済**: Stripe（購読 / 請求 / Webhook 管理）  
- **ドメイン / ネットワーク**: Cloudflare Registrar + Cloudflare CDN（WAF, DDoS 対策, Caching）  
- **コスト配慮**: R2 / Workers / Images の無料枠を最大活用し、ストレージ・配信コストをほぼゼロに抑える設計を常に検討する。

Issue を書く際は、対象マイクロサービスがこのスタックのどの層を担当するかを明記し、エッジデプロイを阻害しないライブラリ選定・I/O 設計を指示すること。

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
   - 外部インターフェース（REST, メッセージング等）は contracts/ 配下にヘッダ・スキーマを残す。
4. **Idempotent な作業手順**  
   - 初期化・テストスクリプトは複数回実行しても破壊的にならないこと。  
   - 破壊的操作が必要な場合はバックアップとロールバック方法を Issue 内に明記する。
5. **ガードレール**  
   - `rm -rf`, `git reset --hard`, 機密ファイルアクセスは禁止（AGENTS.md 参照）。  

---

## 5. 作業スコープ定義
- **想定アウトプット**  
  - `src/` 配下の実装コード  
  - `tests/unit` / `tests/integration` / `tests/e2e` のテストケース  
  - `scripts/`（サービス & ルート）のテストコマンド更新  
  - 関連ドキュメント（ExecPlan, spec, checklists, contracts 等）の更新
- **除外事項**  
  - `<明確に対象外としたい範囲を記載>`  
- **依存関係 / ブロッカー**  
  - `<前提タスクや外部要素を列挙>`

---

## 6. 成功条件 & 検証コマンド
- **動作確認**  
  - `<例> ./scripts/run_all_unit_tests.sh`  
  - `<例> ./scripts/run_all_e2e_tests.sh`  
  - `<例> curl -i http://localhost:8080/health`
- **期待される結果**  
  - `<各コマンドの成功条件、HTTP ステータス、ログ出力などを明記>`
- **ログ提出**  
  - 実行コマンドと要約結果を Issue コメントで報告し、ExecPlan の Validation セクションにも反映する。

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
`<特記事項、利用するライブラリ制約、運用上の注意点などを記載>`

---

> **補足**: Issue 内のすべての記述は、Jules AI エージェントが単独でリポジトリ全体を理解し再開できる水準で具体的に記述してください。文責者は Issue 作成日・氏名を最後に追記することを推奨します。
