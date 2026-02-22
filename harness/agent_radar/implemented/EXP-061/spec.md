# EXP-061 Autonomous Implementation Spec

- Source: `anthropic_engineering`
- Title: [anthropic_engineering] FeaturedQuantifying infrastructure noise in agentic coding evalsInfrastructure configuration can swing agentic coding benchmarks by several percentage points—sometimes more than the leaderboard gap between top models.
- Link: https://www.anthropic.com/engineering/infrastructure-noise
- Themes: mcp, skills, environment, evals

## Goal
記事由来の知見を、再実行可能なハーネス実装としてリポジトリへ定着させる。

## Acceptance
- autogrow 実行で同じ結果に収束する
- validate/garden が継続して成功する
- 生成物が SoR 配下で追跡可能である

