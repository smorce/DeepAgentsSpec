# 指示

AI がツールを動的に発見・学習・実行できるような仕組みを導入します。具体的には以下の3つです。

- コンテキスト肥大には `Tool Search Tool`
- 大きな中間結果や多段ワークフローには `Programmatic Tool Calling`
- パラメータエラーには `Tool Use Examples`

# Tool Search Tool

Tool Search Tool はツール定義をすべて事前ロードするのではなく、必要に応じて検索してロードする仕組みである。
初期ロード時には name, description のみを読み込み、必要になった段階で SKILL.md の本文を展開します。

# Programmatic Tool Calling

Programmatic Tool Callingは、AIがコード実行環境内でツールをpyスクリプトとして呼び出し、ログやテーブルなど大きな中間結果をコンテキストに入れる前に集計・フィルタする仕組みである。
つまり、やりたいことを事前にpyスクリプトとして作成しておき、AIは必要に応じて「uv run --link-mode=copy script_A.py --引数」で実行します。
script_A.py の中身や中間結果を読み込むとコンテキストが圧迫されるため、AIはスクリプトの実行結果のみを受け取ります。
script_A.pyはスクリプト内で成果物を保存します。
例えば経費データ2,000行・200KB相当を扱うタスクでも、最終的な違反ユーザーのリスト1KBだけをモデルに戻せるため、劇的にトークン効率が改善します。

# Tool Use Examples

Tool Use Examplesは、ツール定義にinput_examplesとして具体的な入力例を付与し、JSON Schemaでは表現しづらい使用パターンをモデルに示す機能である。
期限付きのクリティカル障害チケットやラベル付き機能要望、タイトルのみの内部タスクといった例を並べることで、日付形式やID規約、オプションパラメータの組み合わせなどを暗黙的に共有できる。


まずAIを起動させると AGENTS.md を読み込むわけですが、AGENTS.md の中にどんなSkillを持っているのかを記述します。これは人間が記述するべき内容です。
具体的には
```
tools:
  - name: get_team_members
    description: "…"
  - name: get_expenses
    description: "…"
  - name: get_budget_by_level
    description: "…"
```
のような内容を記述する予定です。このメタデータをもって必要に応じてツールをロードします。
DeepAgentsSpec のルートディレクトリに skills ディレクトリを作って各種ツールを入れていきたいです。

この仕組みを DeepAgentsSpec に導入したいです。意味が分からなければ質問してください。