# Feature Specification: F-SYS-010 公式ブログ限定ソースレーダー

## Overview

指定6ブログのみを定点観測し、最新記事の差分をリポジトリ内SoRへ保存する。

## Functional Requirements

- FR-010-001: 収集対象は以下URL群のみであること。
  - https://qwenlm.github.io/blog/
  - https://deepseek.ai/blog/
  - https://sakana.ai/blog/
  - https://huggingface.co/blog/
  - https://developers.openai.com/blog/
  - https://www.anthropic.com/engineering/
- FR-010-002: RSS が利用可能なサイトは RSS を優先する。
- FR-010-003: RSS がない場合は HTML から記事リンクを抽出する。
- FR-010-004: 差分（新規記事）を `harness/agent_radar/new-items.json` に出力する。

## Non-Functional Requirements

- NFR-010-001: 失敗しても他ソースの収集を継続する。
- NFR-010-002: 実行結果は `harness/AI-Agent-progress.txt` に追記する。

## Success Criteria

- SC-010-001: 6ソースすべてについて `snapshot-latest.json` に状態が記録される。
- SC-010-002: 2回目以降の実行で差分比較が行われる。
