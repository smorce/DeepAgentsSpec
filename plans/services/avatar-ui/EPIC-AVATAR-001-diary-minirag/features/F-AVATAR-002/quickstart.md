# Quickstart: F-AVATAR-002

この手順は avatar-ui だけを変更し、日記確定時にプロファイル更新が行われることを確認する。

## 前提

- MiniRAG API が起動している
- avatar-ui の server と app が起動できる（`services/avatar-ui/README.ja.md` を参照）
- プロファイルは単一ファイルで管理される

## 手順

1. avatar-ui server を起動する

   例:

     cd services/avatar-ui/server
     uv run --link-mode=copy python main.py

   必要に応じて `services/avatar-ui/settings.json5` の `profiling` セクションで
   プロファイリングモデルと最低信頼度を調整する。

2. avatar-ui app を起動する

   例:

     cd services/avatar-ui/app
     npm install
     npm run dev

3. UI を開き、ユーザー発話を含む会話を行う

4. 「会話確定」ボタンを押す

5. プロファイル更新が行われることを確認する

   - `services/avatar-ui/profiling/user_profile.yaml` を開き、空欄だった項目が更新されていること

6. profiling を失敗させた場合、UI に警告メッセージが表示されることを確認する

## 期待結果

- 会話確定後にプロファイルが更新される
- 既存の非空値が空で上書きされない
- profiling 失敗時は UI に警告表示が出る
