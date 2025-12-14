---
description: Ingest a natural-language product description, fan-out epics/features, update harness/feature_list.json, scaffold spec/checklist files, and then hand off to /speckit.specify for full spec writing.
handoffs:
  - label: Write Specs For Each Feature
    agent: speckit.specify
    prompt: >
      For every newly created feature ID, run /speckit.specify --feature-id <ID> "<original or feature-specific description>"
      to populate spec.md. Use the feature title/description from bootstrap output when available.
scripts:
  sh: scripts/bash/auto-generate-features.sh {ARGS}
---

## 実行手順

1. `$ARGUMENTS` をそのままプロダクト説明として扱い、次のコマンドを **必ず実行**:  
   ```bash
   scripts/bash/auto-generate-features.sh --description "$ARGUMENTS"
   ```  
   - 失敗したらエラーメッセージを読み、必要に応じて再実行
2. コマンドが返す JSON から `new_features[].id` を取得。  
3. 生成結果として、新規エピック/フィーチャ ID と `spec.md` / checklist のパスをユーザーに報告する。  
4. `/speckit.specify --feature-id F-XXX-YYY "<説明>"` を実行するのはユーザーの役割とし、自動では実行しない。  
5. エラーが出た場合は、Codex が自己修復（再実行・不足パス作成など）を試み、最終的にユーザーが `/speckit.specify` を続行できる状態を保証する。

## User Input

```
$ARGUMENTS
```

## フロー概要

1. ユーザーが作りたいアプリケーションを自然文で説明する（`/speckit.bootstrap-features "説明文"` を想定）。  
2. このテンプレートをトリガーすると、`auto-generate-features.sh` が LLM を用いてエピック／フィーチャ一覧（JSON）を生成し、`harness/feature_list.json` にマージする。  
3. 各フィーチャについて `create-new-feature.sh` を実行し、`spec.md` と `checklists/requirements.md` の枠を作成する（「登録＋枠作り」）。  

## 出力指示

- エピックとフィーチャを JSON で返すこと。  
- 可能ならサービス担当（`api-gateway`, `user-service`, `billing-service` など）を振り分ける。  
- 各フィーチャにはタイトル・短い説明・担当サービスリストを含める。  
- ID 採番はスクリプト側で行うため、LLM 側で ID を固定しない。  

## 期待する成果物

- 更新済み `harness/feature_list.json`（新規エピック・フィーチャ追記、`spec_path` / `checklist_path` 付与）。  
- 各フィーチャの `spec.md` と `checklists/requirements.md` が所定パスに生成済み。  
- 次のステップで `/speckit.specify` を実行するためのフィーチャ ID 一覧。  

## 注意

- 実際の仕様本文はこのステップでは書かない。`specify` フェーズで埋める。  
- 既存 ID と衝突する場合はスキップし、ログに警告を残す。  