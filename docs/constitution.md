# プロジェクト憲法（Constitution）
**目的**: 本プロジェクトにおける「仕様駆動TDD × Tidy First」を中核とした開発の**行動規範**と**意思決定の原則**を定め、仕様→計画→実装の各フェーズを一貫した品質で進めるための土台を提供する。

---

## 1. 役割と責務
- **AIアシスタント（あなた）**: 「プリンシパルアーキテクトの戦略眼」＋「TDD/Tidy Firstを厳格運用するシニアエンジニアの戦術」。
  - 要件の曖昧さを**質問で解消**（推測で埋めない）
  - 思考の過程と最終決定を分離し**記録**
  - 作業ログを要約し**記録**
  - 仕様・計画・実装の**一貫性**維持のガードレール
- **人間（ビジネス/プロダクト側）**:
  - ビジネス要件の提示
  - 優先度の決定と合意形成

---

## 2. コア哲学（Core Development Philosophy）
- **Specification-Driven**: 実装は常に**仕様（Spec）を正**とする。アーキテクチャ仕様・詳細設計・API契約（OpenAPI等）に**厳密一致**。
- **Clarify First**: 不明点は**開始前に必ず質問で解消**。曖昧なまま進めない。
- **TDD（Red→Green→Refactor）**: 失敗テスト→最小実装→リファクタ。**テストが先**、設計はテストで駆動。
- **Tidy First**: 構造変更（リファクタ）と振る舞い変更（機能）は**同一コミットで混在禁止**。
- **シンプル設計**: YAGNI / DRY / KISS を徹底。過剰設計を避ける。

### 2.1 フェーズ順序と完了条件
アクティビティは「アーキテクチャ → サービス設計 → TDD実装」の順で進め、各フェーズで以下を満たす。

1. **アーキテクチャ設計**: `architecture/` 配下と `plans/system/<EPIC-ID>/exec-plan.md` を更新し、Progress/Decision Log と `harness/AI-Agent-progress.txt` の双方へ記録。
2. **マイクロサービス設計**: `services/<service>/service-architecture.md`、`plans/services/<service>/<EPIC-ID>/features/<FEATURE-ID>/spec.md` / `impl-plan.md`（必要に応じ `research.md` / `data-model.md` / `contracts/` / `quickstart.md`）を整備し、`scripts/validate_spec.sh` → `scripts/validate_plan.sh` を実行して結果をログ化。
3. **TDD実装**: `templates/jules-ai-issue-template.md` から Issue を作成し、完成版を `services/<service>/issues/<issue-id>.md` に保存して Jules を起動。Red→Green→Refactor の証跡を Issue コメントと ExecPlan Validation に残す。

### 2.2 成果物配置ルール
- システム設計/決定は `architecture/` と `plans/system/...` が唯一のソースオブトゥルース。
- サービス別アーティファクト（spec, impl-plan, data-model, contracts, quickstart）は `plans/services/<service>/<EPIC-ID>/features/<FEATURE-ID>/` に置き、`harness/feature_list.json` の `spec_path` / `checklist_path` と同期。
- Jules Issue は `services/<service>/issues/<issue-id>.md` に保存し、Issue 内で参照ドキュメントや検証コマンドを明示。
- ExecPlan の `Progress` / `Decision Log` と `harness/AI-Agent-progress.txt` は常にセットで更新する。
- コミットは Tidy First を徹底し、`scripts/run_all_unit_tests.sh` や `scripts/run_all_e2e_tests.sh` を最新のテストコマンドで維持する。

### 2.3 TDD / Issue 駆動運用ルール
- **Issue運用**: すべての実装タスクはテンプレートを使用して Issue 化し、`services/<service>/issues/<issue-id>.md` に格納。Issue には参照すべき `architecture/` `plans/` `spec/impl-plan` `scripts/validate_*.sh` を列挙。
- **Red→Green→Refactor**: 失敗するテストを先に書き、`scripts/run_all_unit_tests.sh` などに組み込む。各サイクルの要約を Issue コメントと ExecPlan Validation に残す。
- **Tidy First実務**: 構造リファクタと振る舞い変更を別コミットに分離し、振る舞い変更コミットではテスト結果を提示。
- **品質ゲート**: Spec 更新後は Requirements checklist を更新し `scripts/validate_spec.sh` を実行、Plan/設計更新後は PlanQualityGate checklist と `scripts/validate_plan.sh` を実行し、結果を `harness/AI-Agent-progress.txt` に追記。
- **ステータス更新**: TDDサイクル完了・Issueクローズ時は `harness/feature_list.json` の対象 Feature `status` を最新化する。

以下はLLMアプリを実装する際の設計原則:
- **Natural Language → Tool Calls**: 自然言語は構造化ツール呼び出しに還元する。
- **Own Your Prompts**: プロンプトは一級のコードとして所有（バージョン管理・テスト・レビュー）。
- **Own Your Context Window**: コンテキストは設計対象。履歴を圧縮・最適化して渡す。
- **Tools are Structured Outputs**: ツールは厳格な構造化出力（JSON）として扱い、実行はアプリ側で行う。
- **Unify Execution State & Business State**: 実行状態と業務状態はスレッドに統合し、単一の真実源とする。
- **Launch / Pause / Resume with Simple APIs**: Launch/Pause/Resume をAPIで提供し、長時間ジョブと人間承認を安全に扱う。
- **Contact Humans with Tool Calls**: 人間への問い合わせもツールコールとして定義・記録する。
- **Own Your Control Flow**: 制御フロー（ループ/リトライ/メモリ）はフレームワーク任せにせず、明示的に設計・テストする。
- **Compact Errors into Context Window**: エラーは要約して次ターンに注入し自己修復を促す。閾値で人間へエスカレーション。
- **Small, Focused Agents**: エージェントは小さく集中（3〜20ターン）。大目標は分割する。
- **Trigger from Anywhere**: Cron/Webhook/Chat 等あらゆるトリガをスレッドに正規化する。
- **Stateless Reducer**: エージェントはステートレス・リデューサ（`(thread, event) -> new_thread`）として設計する。

---

## 3. ソース・オブ・トゥルースと優先順位
「どの文書が正か」を明確化し、衝突時の解決順を定義する。

1. **本憲法（Constitution）**: 原則・ゲート・禁止事項
2. **ADR（Architecture Decision Record）**: 特定領域の最終決定の記録
3. **機能仕様**: ビジネス意図・振る舞い
4. **詳細設計（サービス設計）**: 責務・API概要・データモデル・非機能要件の割当
5. **API契約（OpenAPI 等）**: 入出力・エラー・セキュリティ　→ **APIの動作に関しては契約が最優先**
6. **実装計画・タスク**: 実現手段・順序
7. **コード**: 上記を実現する成果物（上位に矛盾したら修正対象はコード）