# EXP-019 Autonomous Implementation Plan

## Hypothesis
記事知見（mcp, skills, observability）を control_system の改善へ反映すると、品質ゲートと自律実行の信頼性を継続的に高められる。

## Steps
1. Backlog item を実装対象として確定する
2. 状態退避ポリシーを `state-strategy.json` に固定する
3. 監視ターゲットと黄金律を機械更新する
4. autogrow で validate/garden まで実行する

## Verification
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

