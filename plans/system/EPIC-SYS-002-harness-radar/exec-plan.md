# EPIC-SYS-002-HARNESS-RADAR: エージェントハーネス継続進化のSoR構築

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

本ドキュメントは `PLANS.md` に従って維持・更新します。  
本エピックの設計インデックスは `plans/system/EPIC-SYS-002-harness-radar/design/index.md` です。

## Purpose / Big Picture

このエピックの目的は、AIエージェント活用の最新知見を、外部メモではなくリポジトリ内部に継続的に取り込み、検証し、ルール化し、維持できる仕組みを作ることです。  
完成後は、指定6ブログのみを定期収集し、差分検知、評価バックログ化、黄金律への昇格判断、ドキュメントガーデニングまでを機械的に回せます。

## Related Features / Specs

- F-SYS-010: 公式ブログ限定ソースレーダー
  - Spec: `plans/system/EPIC-SYS-002-harness-radar/features/F-SYS-010/spec.md`
- F-SYS-011: フィードバックループと制御システム
  - Spec: `plans/system/EPIC-SYS-002-harness-radar/features/F-SYS-011/spec.md`
- F-SYS-012: 状態管理・永続化・差し替え表現
  - Spec: `plans/system/EPIC-SYS-002-harness-radar/features/F-SYS-012/spec.md`

## Progress

- [x] (2026-02-13 00:00Z) EPIC-SYS-002 の ExecPlan と design index を作成した。
- [x] (2026-02-13 00:00Z) 6ブログ限定のソース収集SoR（設定・状態・差分ファイル）を追加した。
- [x] (2026-02-13 00:00Z) `update/validate/garden` の制御ループ用スクリプトを追加した。
- [x] (2026-02-13 00:00Z) 状態永続化と差し替え表現の仕様を `docs/agent-harness/` に追加した。
- [x] (2026-02-13 11:27Z) `harness/agent_radar/radar_ops.py` に制御ループを統合し、`validate` と `cycle` の実行成功を確認した。
- [x] (2026-02-13 11:40Z) `new-items.json` から `experiment_backlog.json` へ自動起票する `backlog` モードを追加した。
- [x] (2026-02-13 11:40Z) GitHub Actions 日次実行ワークフローを追加した。
- [x] (2026-02-13 15:30Z) `EPIC-SYS-001-foundation` の実体と参照を削除し、現行SoRを `EPIC-SYS-002` に一本化した。

## Surprises & Discoveries

- Observation: 指定URLのうち、形式が RSS と HTML に分かれており、単一パーサでは安定しない。
  Evidence: `qwenlm.github.io` / `sakana.ai` / `developers.openai.com` / `huggingface.co` はRSS取得可能、`anthropic.com/engineering` はHTML抽出が必要。
- Observation: 制御ループ実体を `scripts/` 配下へ分散すると、運用中に参照ズレが起きやすい。
  Evidence: 実行入口の記述が複数ファイルで不整合を起こしたため、`radar_ops.py` へ一本化した。

## Decision Log

- Decision: ソース設定の唯一の真実源を `harness/agent_radar/official_sources.json` に固定する。
  Rationale: 許可ドメインと収集対象の境界を機械検証可能にするため。
  Date/Author: 2026-02-13 / codex

- Decision: 収集結果は `state.json` と `snapshot-latest.json` に分離して保存する。
  Rationale: 差分比較用の最小状態と、人間可読スナップショットを分離することで運用性を上げるため。
  Date/Author: 2026-02-13 / codex

- Decision: 状態退避は「ホット状態JSON + コールドJSONL」の二層にする。
  Rationale: エージェント再開の高速性と監査可能性を両立するため。
  Date/Author: 2026-02-13 / codex

- Decision: 制御ループは `harness/agent_radar/radar_ops.py` の単一エントリポイントに統合する。
  Rationale: `update/validate/garden/cycle` の実行インターフェースを固定し、運用ドキュメントとの整合を維持しやすくするため。
  Date/Author: 2026-02-13 / codex

- Decision: `cycle` に `backlog` ステップを組み込み、差分検知と実験起票を機械的に連結する。
  Rationale: `new-items.json` の見落としを防ぎ、知見取り込みを人手待ちにしないため。
  Date/Author: 2026-02-13 / codex

- Decision: `EPIC-SYS-001-foundation` を廃止し、システムレベルのSoR管理対象を `EPIC-SYS-002-HARNESS-RADAR` へ一本化する。
  Rationale: 現行運用と無関係な初期土台エピックを残すと、エージェント参照時にノイズとなるため。
  Date/Author: 2026-02-13 / codex

## Outcomes & Retrospective

このエピックで、指定6ブログ限定の収集・差分検知・検証・ガーデニングを回す最小ハーネスができた。  
次の段階は、収集した新規項目を自動で Feature 候補へ変換し、E2E評価と黄金律昇格を完全自動化すること。

## Context and Orientation

変更対象は、`harness/agent_radar/`（SoRデータと制御ループ）、`docs/agent-harness/`（運用仕様）、`architecture/`（全体設計）です。  
実装コードを先に増やすのではなく、まず知識更新の制御面を整備します。

## Plan of Work

1. 公式ブログ限定のソース定義を作る。
2. 収集・差分検知・状態保存スクリプトを追加する。
3. 妥当性検証スクリプトを追加する。
4. 差分から実験バックログへ自動起票する。
5. ドキュメントガーデニングスクリプトを追加する。
6. 全体制御スクリプトで一連処理を束ねる。
7. アーキテクチャ文書と決定ログに反映する。

## Concrete Steps

1. `harness/agent_radar/official_sources.json` に6ソースを定義する。
2. `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update` で RSS/HTML 収集と差分検知を実装する。
3. `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate` で構造・許可URL・境界違反を検証する。
4. `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog` で `new-items.json` を `experiment_backlog.json` へ反映する。
5. `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden` で SoR 文書のプレースホルダー混入を検出する。
6. `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle` で `update -> validate -> backlog -> garden` を直列実行する。

## Validation and Acceptance

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle` が 0 で終了し、`harness/agent_radar/snapshot-latest.json` を更新する。
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate` が 0 で終了し、`OK` を返す。
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog` が 0 で終了し、差分のみを実験バックログへ追加する。
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden` が 0 で終了し、対象文書に TODO/NEEDS CLARIFICATION がない。
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle` が 0 で終了し、`harness/AI-Agent-progress.txt` に実行ログが残る。

## Idempotence and Recovery

各スクリプトは再実行可能です。  
失敗時は `harness/agent_radar/state.json` を直近コミットへ戻し、再実行します。  
誤検知が発生した場合は `official_sources.json` の `allowed_entry_prefixes` を調整して再収集します。

## Artifacts and Notes

- Epic design index: `plans/system/EPIC-SYS-002-harness-radar/design/index.md`
- Source of Record root: `harness/agent_radar/`
- Ops docs: `docs/agent-harness/`

## Interfaces and Dependencies

- External inputs: 指定6ブログの公開ページ/RSSのみ。
- Internal interfaces:
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`
  - `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle`
