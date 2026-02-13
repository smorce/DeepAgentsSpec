# Operations

## 対象

本ドキュメントは EPIC-SYS-001 の Agent Harness SoR（source radar + control loop）の運用手順を定義します。

## 日次運用

1. 収集・検証・バックログ同期・実装・ガーデニングを実行

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow
```

2. 新規差分を確認

```bash
cat harness/agent_radar/new-items.json
```

3. レポート確認

```bash
ls docs/reports/source-radar/
```

## 自動実行

- GitHub Actions: `.github/workflows/agent-radar-daily.yml`
- 実行時刻: 毎日 `00:15 UTC`
- PR品質ゲート: `.github/workflows/quality-gates.yml`
  - Spec/Plan/SoR/Doc/Test の検証をブロッキング実行

## 障害対応

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow` 失敗:
  - ネットワークまたはサイト構造変化を疑う。
  - `harness/agent_radar/snapshot-latest.json` の `errors` を確認する。

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate` 失敗:
  - 許可外リンク混入または SoR構造破損。
  - `official_sources.json` と `snapshot-latest.json` の境界を確認する。
  - `mutation` の hash 不整合時は `--mode implement` または `--mode autogrow` を再実行し整合を回復する。
  - `monitoring_targets.json` が存在する場合は `metrics/latest.json` / `monitoring_results.json` の鮮度と整合を確認する。

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog` 失敗:
  - `new-items.json` または `experiment_backlog.json` の構造崩れ。
  - `new_items` / `items` が配列か確認する。

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement` 失敗:
  - `experiment_backlog.json` の各項目に `id` が存在するか確認する。
  - `harness/agent_radar/golden_rules.json` / `monitoring_targets.json` の構造崩れを確認する。

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden` 失敗:
  - 対象文書の `TODO:` / `NEEDS CLARIFICATION` / `プレースホルダー` を除去する。

- `scripts/run_all_e2e_tests.sh`:
  - デフォルトでは UI モックシナリオのみ実行される。
  - live API シナリオが必要な場合は `RUN_LIVE_MINIRAG_E2E=1` を指定する。

## エスカレーション条件

以下は人間レビュー必須:

- 公式URL変更が必要な場合
- 差し替え表現や状態スキーマの後方互換が壊れる場合
- 黄金律に昇格するルール変更
