# EXP-083 Autonomous Implementation Spec

- Source: `openai_developers`
- Title: [openai_developers] Shell + Skills + Compaction: Tips for long-running agents that do real work
- Link: https://developers.openai.com/blog/shell-skills-compaction
- Themes: mcp, skills, observability, scalability, reliability, context, environment, evals, safety, feedback

## Goal
記事由来の知見を、再実行可能なハーネス実装としてリポジトリへ定着させる。

## Acceptance
- autogrow 実行で同じ結果に収束する
- validate/garden が継続して成功する
- 生成物が SoR 配下で追跡可能である

