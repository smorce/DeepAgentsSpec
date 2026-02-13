# Feature Specification: F-SYS-011 フィードバックループと制御システム

## Overview

収集結果を検証し、ドキュメントガーデニングを含む制御ループを定常運用する。

## Functional Requirements

- FR-011-001: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle` で update/validate/backlog/implement/garden を順次実行できる。
- FR-011-002: 許可外URL混入を `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate` が検知できる。
- FR-011-004: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog` で `new-items.json` の差分を `experiment_backlog.json` に起票できる。
- FR-011-005: `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow` で収集から実装までを無人で完走できる。
- FR-011-003: SoR文書の TODO/NEEDS CLARIFICATION を検知できる。

## Non-Functional Requirements

- NFR-011-001: 失敗時に非0で終了し、CIゲートとして利用可能である。
- NFR-011-002: 実行ログは短く機械判読可能である。

## Success Criteria

- SC-011-001: 1コマンドで制御ループ全体を再現できる。
- SC-011-002: 許可外URLを混入させると validate が失敗する。
