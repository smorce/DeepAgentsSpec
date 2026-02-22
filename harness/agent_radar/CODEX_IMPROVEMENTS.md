# Codex CLI 実行機能の改善

## 実施日
2026-02-19

## 概要
`radar_ops.py` の Codex CLI 実行機能に以下の改善を実施しました：

1. `.codex/config.toml` の設定が正しく適用されるように修正
2. LLM API エラー（429, 5xx, タイムアウト等）に対するリトライ機能を追加

## 変更内容

### 1. 新規追加：LLM リトライ設定定数

```python
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 2.0
LLM_RETRY_MAX_DELAY = 60.0
LLM_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
```

### 2. 新規追加：RetryHandler クラス

指数バックオフとジッターを使用したリトライハンドラーを実装：

- **should_retry()**: エラーがリトライ可能かどうかを判定
  - コンテキスト超過エラーは非リトライ（回復不可能）
  - 429, 5xx, タイムアウト、接続エラーはリトライ対象
  
- **get_delay()**: リトライ前の待機時間を計算（指数バックオフ + ジッター）

### 3. 改善：run_codex_exec() 関数

#### 主な変更点

1. **リトライロジックの追加**
   - `RetryHandler` を使用してリトライ可能エラーを自動的に再試行
   - 最大3回までリトライ（初回 + 3回）
   - 各リトライ間に指数バックオフで待機

2. **config.toml の適用**
   - `cwd=str(ROOT)` を指定してリポジトリルートで実行
   - これにより `.codex/config.toml` が trusted 時に読み込まれる
   - 環境変数 `CODEX_HOME`, `HOME`, `USERPROFILE` を明示的に設定

3. **構造の改善**
   - `run_codex_exec()`: リトライロジックを含むラッパー関数
   - `_run_codex_exec_once()`: 1回の実行を担当する内部関数

## 動作説明

### 正常時のフロー

```
1. run_codex_exec() 呼び出し
2. RetryHandler 初期化
3. _run_codex_exec_once() 実行
   - リポジトリルートを cwd に指定
   - .codex/config.toml が読み込まれる
   - codex exec コマンド実行
4. 成功時は結果を返す
```

### エラー時のフロー

```
1. _run_codex_exec_once() でエラー発生
2. RetryHandler.should_retry() でリトライ可否を判定
   - コンテキスト超過: リトライせず即座に失敗
   - 429/5xx/タイムアウト: リトライ対象
3. リトライ対象の場合:
   - RetryHandler.get_delay() で待機時間を計算
   - 待機後に再実行（最大3回まで）
4. 最大リトライ回数到達で失敗
```

## 適用される config.toml の設定

`.codex/config.toml` に以下の設定が記述されている場合、自動的に適用されます：

```toml
model = "gpt-5.3-codex"
model_reasoning_effort = "medium"
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "live"
```

## テスト方法

### 基本動作確認

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update --collector codex
```

### リトライ動作確認

一時的に API エラーが発生した場合、自動的にリトライされることを確認：

1. ネットワーク不安定時に実行
2. ログに `codex exec retry` メッセージが出力されることを確認
3. 最終的に成功 or 最大リトライ回数で失敗することを確認

## 今後の拡張可能性

- リトライ回数や待機時間を環境変数で設定可能にする
- リトライ可能エラーのパターンを外部ファイルで定義可能にする
- リトライ履歴を metrics に記録する

## 関連ファイル

- `harness/agent_radar/radar_ops.py`: 本体実装
- `.codex/config.toml`: Codex CLI 設定
- `docs/agent-harness/guide.md`: ハーネス運用ガイド
