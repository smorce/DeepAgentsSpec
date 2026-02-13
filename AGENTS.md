# AGENTS.md

このファイルは **エージェント運用の目次** です。  
詳細ルールは以下を正とします。

- 基本原則: `docs/constitution.md`
- 実務手順: `docs/onboarding.md`
- ハーネス運用: `docs/agent-harness/`
- システム設計: `architecture/`
- 実行計画: `plans/system/` と `plans/services/`

## 1. 目的

- 人間は意図・優先順位・受け入れ条件を定義する。
- エージェントは仕様駆動で実装・検証・記録を行う。
- リポジトリ内成果物を SoR（System of Record）として維持する。

## 2. フェーズ順序（必須）

1. アーキテクチャ設計
   - 更新先: `architecture/` と `plans/system/<EPIC-ID>/exec-plan.md`
2. サービス設計
   - 更新先: `services/<service>/...` と `plans/services/<service>/<EPIC-ID>/features/<FEATURE-ID>/`
3. TDD実装
   - `templates/jules-ai-issue-template.md` を元に Issue を作成し、`services/<service>/issues/<issue-id>.md` に保存

## 3. 品質ゲート（必須）

実行順序を守ること。

```bash
bash scripts/format_or_lint.sh
bash scripts/validate_spec.sh
bash scripts/validate_plan.sh
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate
bash scripts/garden_agent_docs.sh
bash scripts/run_all_unit_tests.sh
bash scripts/run_all_e2e_tests.sh
```

- Spec更新後は `validate_spec.sh` を必ず通す
- Plan更新後は `validate_plan.sh` を必ず通す
- ハーネス更新後は `radar_ops.py --mode validate` を必ず通す

## 4. TDD / Tidy First

- Red → Green → Refactor を厳守
- 構造変更と振る舞い変更を同一コミットに混在させない
- テスト実行結果を `harness/AI-Agent-progress.txt` に残す

## 5. 記録義務

- 重要判断は以下の双方に記録
  - 各 ExecPlan の `Decision Log`
  - `docs/decisions.md`
- 進捗は以下の双方に記録
  - 各 ExecPlan の `Progress`
  - `harness/AI-Agent-progress.txt`
- Feature完了時は `harness/feature_list.json` の `status` を更新

## 6. 成果物配置ルール

- システム設計: `architecture/` と `plans/system/...`
- サービス仕様: `plans/services/<service>/<EPIC-ID>/features/<FEATURE-ID>/`
- 契約: feature配下 `contracts/`
- 実装ガイド: feature配下 `quickstart.md`
- Jules指示書: `services/<service>/issues/<issue-id>.md`

## 7. 禁止事項（要約）

- 破壊的操作: `rm -rf`, `git reset --hard`, `git rebase`（明示許可なし）
- 機密アクセス: `.env*`, 秘密鍵, `secrets/` 配下
- 推測実装: 要件が曖昧なら必ず確認してから進める

## 8. Python / uv

OneDrive 環境を前提に、`uv` は常に copy モードで実行する。

```bash
uv run --no-project --link-mode=copy <command>
```

## 9. ハーネス運用の入口

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2
```

補助モード:

- `--mode update`
- `--mode validate`
- `--mode backlog`
- `--mode implement`
- `--mode garden`

## 10. 迷ったときの参照順

1. `docs/constitution.md`
2. 対象EPICの `exec-plan.md`
3. 対象FEATUREの `spec.md` / `impl-plan.md`
4. `docs/onboarding.md`
5. `docs/agent-harness/*.md`

この順で矛盾を解消し、判断を記録してから実装すること。
