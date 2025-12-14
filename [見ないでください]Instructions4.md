XXX がこのコードベースと整合しているかチェックしてください。細かい点も見逃さないでください。このスクリプトが足りないとか、PATH が間違っているとか細かい点でも矛盾がないか確認してください。



このコードベースの「構造」と「処理フロー」に焦点を当てて解説してください。
ビジネスロジックがどこに記述されており、各モジュールがどのように連携しているかを理解したいです。




templates/commands/specify.md を最初に使ってAIエージェントとやり取りする想定ですが、合っていますか？

─ Worked for 6s ─────────────────────────────────────────────────────────────

• はい、その通りです。TDD／Tidy Firstの流れでも、まず「仕様（spec）」を固めて



› templates/commands/specify.md を最初に使ってAIエージェントとやり取りする想定ですが、合っていますか？

─ Worked for 11s ────────────────────────────────────────────────────────────

はい、合っています。templates/commands/specify.mdは/speckit.specifyコマンドの挙動と手順を定義するテンプレートで、最初にAIエージェントがユーザー入力（機能の自然文説明）を受け取り、scripts/bash/create-new-feature.shなどを実行してspec.mdとchecklists/requirements.mdを生成する起点として使う想定です。

簡潔に流れを整理すると:
- ユーザーが/speckit.specify --feature-id F-XXX-YYY "機能説明" のように叩くと、このテンプレートに沿ってエージェントが動く。
- harness/feature_list.jsonで指定されたfeatureのspec_pathへspec-template.mdをコピーし、チェックリストを作成。
- 生成されたspec.mdをエージェントがユーザー入力に基づき埋め、次段の/speckit.clarify（仕様精緻化）や/speckit.plan（実装計画）へハンドオフする。
したがって「まず仕様を決める」フェーズの正式な入口がこのテンプレートで間違いありません。
