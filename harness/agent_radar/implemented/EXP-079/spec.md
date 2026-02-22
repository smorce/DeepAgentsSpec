# EXP-079 Autonomous Implementation Spec

- Source: `hugging_face`
- Title: [hugging_face] DenseR: Dense Rewards For Free in LLM Reasoning ([huggingface.co](https://huggingface.co/blog/hbXNov/denser?utm_source=openai))
- Link: https://huggingface.co/blog/hbXNov/denser
- Themes: mcp, skills, observability, scalability, reliability, context, environment, evals, safety, feedback

## Goal
記事由来の知見を、再実行可能なハーネス実装としてリポジトリへ定着させる。

## Acceptance
- autogrow 実行で同じ結果に収束する
- validate/garden が継続して成功する
- 生成物が SoR 配下で追跡可能である

