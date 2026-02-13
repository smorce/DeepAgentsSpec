# Agent Harness Control Loop

## ループ構造

1. Detect: 指定ブログの更新を検出する。
2. Verify: 許可境界と構造妥当性を検証する。
3. Curate: 差分を実験バックログへ自動起票する。
4. Encode: 成果を黄金律へ昇格する。
5. Garden: 仕様・計画・運用文書の劣化を修復する。

## 実行コマンド

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle
```

## 失敗時ポリシー

- update 失敗: 対象ソースのみ warning とし、他ソース継続。
- validate 失敗: 終了コード 1 で停止（マージ不可ゲート）。
- garden 失敗: TODO/未確定記法が残っているため修正必須。

## 監視対象

- 新規記事数 (`new_item_count`)
- 収集成功率（source 単位）
- 許可外リンク検出件数
- ドキュメント劣化件数
