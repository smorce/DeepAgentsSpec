# Research: F-AVATAR-001

## Decision 1: 検索ツールはサーバー側で実装し、Gemini のツール呼び出しとして提供する

**Rationale**: UI に検索ロジックを持たせると Gemini からの自律検索を実現しにくい。AG-UI サーバーがツールを提供すれば、Gemini が必要時に検索を実行し、結果を文脈として受け取れる。

**Alternatives considered**:

- UI で常に検索し、結果を Gemini に渡す: 常時検索になりコストとノイズが増える。
- UI に検索ボタンを追加し、ユーザーが明示的に検索: 自律検索という要件を満たさない。

## Decision 2: 会話確定は UI ボタン操作で明示的に行う

**Rationale**: 日記の区切りはユーザーの意図が強く関与するため、明示操作のほうが誤登録を防ぎやすい。

**Alternatives considered**:

- 一定時間の無操作で自動確定: 誤検知で意図しない登録が発生する。
- Gemini が自律的に終了判定: ブラックボックス化しユーザーの制御感が低下する。

## Decision 3: workspace は固定値 `diary` を採用する

**Rationale**: 個人日記用途での単一ワークスペース運用を前提とし、検索の精度と運用の単純性を確保する。

**Alternatives considered**:

- UI で workspace を切り替え: 体験が複雑化し、要件に不要。

