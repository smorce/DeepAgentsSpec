# 基本的な使い方

## Gemini 3.0 Pro の設定方法
CLIではなく、Webブラウザからしか設定できない。
https://forest.watch.impress.co.jp/docs/news/2066962.html

## タスク（セッション）を作成（非同期・並列にいくつでも投げられる）
jules remote new --repo . --session "Issue #12 のバグ修正"
jules remote new --repo . --session "Issue #18 のテスト追加"
jules remote new --repo . --session "Issue #21 のリファクタリング"

## セッション一覧（状態確認）
jules remote list --session    # または --task と書かれている資料もあり

## 完了したセッションの結果をローカルに引き込む
jules remote pull --session 123456   # ここで 123456 はセッション ID

## よりリッチなレビューや diff 確認は：
# - Web UI のタスク画面 / PR 画面
# - CLI の TUI（単に `jules` と打つ）で行う


- Jules は リポジトリルートに AGENTS.md があれば自動的に探して利用する仕様になっている。
- JulesはGoogleが作ったコーディングAIエージェントです。Githubと連携してクラウド上の仮想環境でコーディングを非同期的に自動でコーディングとテストを実施してくれます。
- Claude Code on Web や Codex Web のようなものと思っていいでしょう。
- Jules on Gemini 3 pro のメリット
  - Type Scriptの型解決できないことはない
  - 解決できない永遠のエラーループが発生しない。自力で解決できるようになった
  - Playwrightが動くのでE2Eテストも実行可能
    - しかも Gemini 3 pro対応になってからPlaywright実行が安定している気がする


# 📄 スクリプト例 — Issue タイトルを使って Jules にタスクを送る

以下は Bash シェルスクリプトの例です:
```
#!/usr/bin/env bash
set -e

# GitHub リポジトリのルートで実行
# 未処理の Issue をひとつ取り、そのタイトルを使って Jules タスク起動
# 例: 担当が自分(@me) のオープンな Issue を取る

issue_title=$(gh issue list --assignee @me --state open --limit 1 --json title \
  | jq -r '.[0].title')
if [ -z "$issue_title" ] || [ "$issue_title" = "null" ]; then
  echo "No open issue assigned to me"
  exit 0
fi

echo "Starting Jules task for issue: $issue_title"
jules remote new --repo . --session "$issue_title"
```

ポイント
- gh issue list ... --json title で JSON 出力を得て、jq で最初の Issue のタイトルを取得。
- そのタイトルを、そのまま jules remote new の --session 引数に渡す。
- このスクリプトで、“Issue assigned to me かつ open な最初の Issue を取り → Jules にタスクとして投げる”ことができます。


# Tips
- 大規模な作業を1つのVMで完遂させるのは無理なので、なるべく小さなインクリメンタルに分割する。小粒なテストなら十分成立します。
- 外部APIを叩くみたいな依存関係がある場合Julesでテストができないので、この点を考慮して、マイクロサービスを実装する

- “都合よく通るテスト” を書き換えがちなのでテストコードはこっちで作成する必要がありそう。なのでExecPlan・Specと一緒に対象のテストコード置き場も書いた方が良い。

- Jules は Issue を処理する際に 関連ドキュメントを自動で探索して読み込みます。 （これは公式が明言している“context-aware agent” 機能）。
```この Issue の実装は docs/coding-style.md に従ってください。
あなたに実装を任せたいマイクロサービスは services/api-gateway/EPIC-API-001-routing/ です。ここはVMです。外部との通信は制限されている環境なので注意してください。

  AIエージェント向けにオンボーディング資料を用意しましたので確認してください。→ `docs/onboarding.md`
  以降のセッションでは、README を毎回読み直す必要はなく、`docs/onboarding.md` と各 ExecPlan / spec を見れば十分です。

(以下は精度が出ないときに追記する内容)
仕様は docs/spec/authentication.md を参照してください。
全体アーキテクチャは architecture/ に書いてあります。
必要に応じて、仕様に従って実装を修正してください。

以下を参考にしてください:
- docs/error-handling.md
- docs/coding-style.md
- docs/domain-spec/payment-spec.md
みたいな感じで、オンボーディングだけでなくココでも書いておく。
```
