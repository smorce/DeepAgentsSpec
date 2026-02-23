# Agent Harness 解説書

## この文書の目的

この文書は、`feat/agent-harness-sor-radar` で実装した自律成長ハーネスの全体像を、運用者向けに説明するものです。  
「なにが自律化されているか」「どの成果物が SoR か」「失敗時にどう回復するか」を最短で把握できる構成にしています。

## 1. 全体アーキテクチャ

ハーネスは `harness/agent_radar/radar_ops.py --mode pipeline` をエントリポイントとする制御ループです。

1. `radar`: 6つの公式ブログ本文を分析し、改善アイデアを抽出
2. `analyze`: コードベースとの差分（ギャップ）を分析
3. `review`: 多段レビューループで計画を磨く
4. `execute`: タスク単位の隔離worktreeで改修・検証・証跡生成
5. `validate`: 改修後の整合を再検証
6. `garden`: ドキュメント鮮度を維持
7. `monitoring`: メトリクスと監視評価結果を更新

## 2. System of Record

主要 SoR は次のファイルです。

- ソース/収集:
  - `harness/agent_radar/official_sources.json`
- 実験/実装:
  - `harness/agent_radar/ideas/`
  - `harness/agent_radar/analysis/`
  - `harness/agent_radar/reviews/`
  - `harness/agent_radar/executions/`
  - `harness/agent_radar/knowledge_base.json`
- 品質/監視:
  - `harness/agent_radar/monitoring_targets.json`
  - `harness/agent_radar/monitoring_results.json`
  - `harness/agent_radar/metrics/latest.json`
  - `harness/agent_radar/metrics/history.jsonl`
- 回復/監査:
  - `harness/agent_radar/self_heal_log.json`
  - `docs/reports/source-radar/codex-exec/`
- タスク隔離ハーネス:
  - `harness/worktree/worktree_ops.py`
  - `harness/worktree/runs/`

## 3. 自己修復の仕組み

ステップ失敗時は `--self-heal-max-retries` 回まで自動修復を試行します。

- フォールバックで失敗を隠蔽しない（V1への降格なし）
- 整合回復（監視鮮度更新、文書同期）を行ったうえで再試行
- 回復不能時は失敗を明示し、証跡を SoR に残す

修復履歴は `harness/agent_radar/self_heal_log.json` に永続化されます。

## 4. 監視の実接続

`pipeline` 実行ごとに、実測メトリクスを生成して監視評価まで行います。

- メトリクス生成:
  - `v2.ideas_extracted`
  - `v2.analyses_completed`
  - `v2.ideas_adopted`
  - `v2.ideas_rejected`
  - `v2.reviews_approved`
  - `v2.executions_completed`
- 保存先:
  - `harness/agent_radar/metrics/latest.json`
  - `harness/agent_radar/metrics/history.jsonl`
- 監視評価:
  - `harness/agent_radar/monitoring_targets.json` を評価
  - 結果は `harness/agent_radar/monitoring_results.json` に保存

## 5. 日次自律実行

GitHub Actions で日次実行されます。

- 定義: `.github/workflows/agent-radar-daily.yml`
- 実行コマンド:
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --collector auto --self-heal-max-retries 2`
- 変更があれば SoR を自動コミット/自動 push

加えて、PR 時には `.github/workflows/quality-gates.yml` で
Spec/Plan/SoR/テストの品質ゲートを強制します。

## 6. 実行コマンド

```bash
# V2パイプライン実行
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode pipeline --collector auto --self-heal-max-retries 2

# レビューループ単独実行
bash scripts/run_v2_review_loop.sh harness/agent_radar/reviews/REV-EXP-084
```

## 7. 運用上の判断ポイント

- `collector=codex` は厳格収集モード（失敗時エラー終了）
- `collector=auto` は運用推奨（V1フォールバックは行わず、失敗は観測する）
- 監視しきい値変更は `monitoring_targets.json` を編集し、`validate` 通過を必須とする
- 自己修復ログの増加は、設計ドリフトの兆候として週次で確認する
- MCP/Skills は取り込みテーマの一例であり、環境・フィードバックループ・制御システム改善へ横展開する
- `monitoring_targets.json` が 1 件以上ある場合、`metrics/latest.json` と `monitoring_results.json` は
  鮮度（36時間以内）と件数整合を保つ必要がある
- `harness/worktree/worktree_ops.py` は、再現→修正→証跡生成を 1 回で回す標準入口として扱う
- V2の不採用アイデアは `ideas/rejected/` に理由付きで保存される（将来の再検討用）
