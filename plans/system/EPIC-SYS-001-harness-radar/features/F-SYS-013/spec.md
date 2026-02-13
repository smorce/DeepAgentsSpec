# Feature Specification: F-SYS-013 自律実装と監視ターゲット生成

## Overview

実験バックログの項目を、無人で実装アーティファクト・監視ターゲット・黄金律へ反映する。

## Functional Requirements

- FR-013-001: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement` で `experiment_backlog.json` の `proposed/ready/planned` 項目を実装済みにできる。
- FR-013-002: 実装時に `harness/agent_radar/implemented/<EXP-ID>/` 配下へ spec/plan/state-strategy を生成する。
- FR-013-003: 実装時に `harness/agent_radar/monitoring_targets.json` を更新し、監視対象を増分追加できる。
- FR-013-004: 実装時に `harness/agent_radar/golden_rules.json` へ重複なしで自動ルールを追加できる。
- FR-013-005: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow` で update から implement まで自律完走できる。

## Non-Functional Requirements

- NFR-013-001: 実装処理は再実行しても重複生成しない（idempotent）。
- NFR-013-002: 生成物はすべて SoR 配下に置き、追跡可能である。

## Success Criteria

- SC-013-001: 実験項目を1件 `ready` にして `implement` 実行すると、`implemented` へ遷移しアーティファクトが生成される。
- SC-013-002: `autogrow` 実行後に `validate` と `garden` が継続して成功する。
