# EXP-001 Autonomous Implementation Plan

## Hypothesis
記事由来の改善仮説をハーネス実装へ反映する。

## Steps
1. Backlog item を実装対象として確定する
2. 状態退避ポリシーを `state-strategy.json` に固定する
3. 監視ターゲットと黄金律を機械更新する
4. autogrow で validate/garden まで実行する

## Verification
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

