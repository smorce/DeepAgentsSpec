# Agent Harness 解説書

## この文書の目的

この文書は、`feat/agent-harness-sor-radar` で実装した自律成長ハーネスの全体像を、運用者向けに説明するものです。  
「なにが自律化されているか」「どの成果物が SoR か」「失敗時にどう回復するか」を最短で把握できる構成にしています。

## 1. 全体アーキテクチャ

ハーネスは `harness/agent_radar/radar_ops.py` をエントリポイントとする制御ループです。

1. `update`: 6つの公式ブログを収集し、差分を検出
2. `validate`: 境界・構造・監視定義・mutation整合を検証
3. `backlog`: `new-items.json` から実験バックログを自動起票
4. `implement`: 実装成果物・黄金律・監視ターゲット・mutationコードを生成
5. `validate`(再): 実装後の整合を再検証
6. `garden`: 文書の placeholder を検出/修復

`autogrow` はこの流れを一括実行します。

## 2. System of Record

主要 SoR は次のファイルです。

- ソース/収集:
  - `harness/agent_radar/official_sources.json`
  - `harness/agent_radar/state.json`
  - `harness/agent_radar/snapshot-latest.json`
  - `harness/agent_radar/new-items.json`
- 実験/実装:
  - `harness/agent_radar/experiment_backlog.json`
  - `harness/agent_radar/implemented/`
  - `harness/agent_radar/mutations/index.json`
  - `harness/agent_radar/mutations/*.py`
- 品質/監視:
  - `harness/agent_radar/golden_rules.json`
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

## 3. 自己改変の仕組み

`implement` ステップは、各 EXP に対して mutation モジュールを生成します。

- 生成先: `harness/agent_radar/mutations/mutation_<exp>.py`
- 登録先: `harness/agent_radar/mutations/index.json`

次回の `update` 実行時に mutation モジュールがロードされ、`new-items.json` のエントリへ自動的にタグ/運用属性を付与します。  
これにより、実装結果が次回以降の収集・選別ロジックへ反映されます。

## 4. 自己修復の仕組み

ステップ失敗時は `--self-heal-max-retries` 回まで自動修復を試行します。

- `update` 失敗: `native` 収集へフォールバック
- `validate` 失敗: 境界逸脱データのトリム、mutation index 補正、監視定義補正
- `backlog`/`implement` 失敗: JSON 構造を正規化して再実行
- `garden` 失敗: TODO/未確定記法を自動置換

修復履歴は `harness/agent_radar/self_heal_log.json` に永続化されます。

## 5. 監視の実接続

`autogrow` 実行ごとに、実測メトリクスを生成して監視評価まで行います。

- メトリクス生成:
  - `autogrow.success`
  - `autogrow.success_rate`
  - `autogrow.recovered_steps`
  - `autogrow.self_heal_actions`
  - `radar.new_item_count` など
- 保存先:
  - `harness/agent_radar/metrics/latest.json`
  - `harness/agent_radar/metrics/history.jsonl`
- 監視評価:
  - `harness/agent_radar/monitoring_targets.json` を評価
  - 結果は `harness/agent_radar/monitoring_results.json` に保存

## 6. 日次自律実行

GitHub Actions で日次実行されます。

- 定義: `.github/workflows/agent-radar-daily.yml`
- 実行コマンド:
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2`
- 変更があれば SoR を自動コミット/自動 push

加えて、PR 時には `.github/workflows/quality-gates.yml` で
Spec/Plan/SoR/テストの品質ゲートを強制します。

## 7. 運用上の判断ポイント

- `collector=codex` は厳格収集モード（失敗時エラー終了）
- `collector=auto` は運用推奨（失敗時 native へフォールバック）
- 監視しきい値変更は `monitoring_targets.json` を編集し、`validate` 通過を必須とする
- 自己修復ログの増加は、設計ドリフトの兆候として週次で確認する
- `monitoring_targets.json` が 1 件以上ある場合、`metrics/latest.json` と `monitoring_results.json` は
  鮮度（36時間以内）と件数整合を保つ必要がある
- `harness/worktree/worktree_ops.py` は、再現→修正→証跡生成を 1 回で回す標準入口として扱う
