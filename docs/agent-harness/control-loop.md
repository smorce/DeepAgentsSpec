# Agent Harness Control Loop

## ループ構造

1. Detect: 指定ブログの更新を検出する。
2. Verify: 許可境界と構造妥当性を検証する。
3. Curate: 差分を実験バックログへ自動起票する。
4. Implement: バックログ項目から実装アーティファクト・監視・黄金律を生成する。
5. Encode: 成果を黄金律へ昇格する。
6. Garden: 仕様・計画・運用文書の劣化を修復する。

## 実行コマンド

```bash
uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2
```

Codex収集を強制したい場合は `--collector codex` を指定する。  
自己修復の試行回数は `--self-heal-max-retries` で制御する。

## 失敗時ポリシー

- update 失敗: `native` 収集にフォールバックして再試行する。
- validate 失敗: 境界逸脱データをトリムして再検証する。
- implement/backlog 失敗: バックログ JSON 構造を自己修復して再試行する。
- garden 失敗: placeholder 行を自動置換して再試行する。
- 修復履歴: `harness/agent_radar/self_heal_log.json` に保存する。

## 監視対象

- 新規記事数 (`new_item_count`)
- 実装完了件数 (`implemented_count`)
- 収集成功率（source 単位）
- 許可外リンク検出件数
- ドキュメント劣化件数
- 自己修復実行回数 (`autogrow.self_heal_actions`)
- 監視評価結果 (`harness/agent_radar/monitoring_results.json`)
