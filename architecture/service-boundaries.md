# サービス境界

## 境界定義

### A. Source Radar

責務:
- 6ブログの更新収集
- 差分検知

非責務:
- 実装コード自体の改変
- 未許可ソースの収集

主な成果物:
- `harness/agent_radar/snapshot-latest.json`
- `harness/agent_radar/new-items.json`

### B. Harness Validator

責務:
- 許可URL境界の検証
- SoR構造の整合性検証

非責務:
- 仕様策定そのもの

主な成果物:
- バリデーション結果（終了コード/標準出力）

### C. Doc Gardener

責務:
- SoR文書の劣化検知（TODO、未確定記法）

非責務:
- 新機能実装

### D. State Persistence

責務:
- ホット状態/コールド状態の分離保存
- 差し替え表現の一貫管理

非責務:
- 機密値の保存

## 境界違反の扱い

- 許可外URLを検出した場合は即失敗（非0終了）。
- 失敗イベントは `harness/AI-Agent-progress.txt` に残す。
