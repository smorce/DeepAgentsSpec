# Quickstart: F-AVATAR-001

この手順は avatar-ui だけを変更し、MiniRAG API を既存のまま利用することを前提にする。

## 前提

- MiniRAG API が起動している（`POST /minirag/documents/bulk`, `POST /minirag/search`）
- avatar-ui の server と app が起動できる（`services/avatar-ui/README.ja.md` を参照）
- workspace は `diary`

## 手順

1. avatar-ui server を起動する

   例:

     cd services/avatar-ui/server
     uv run --link-mode=copy python main.py

2. avatar-ui app を起動する

   例:

     cd services/avatar-ui/app
     npm install
     npm run dev

3. UI を開き、Gemini と日記会話を行う

4. 検索トグルを ON にし、過去日記に関する質問を行う

5. 「会話確定」ボタンを押し、登録結果が表示されることを確認する

## 期待結果

- 登録成功メッセージに doc_id と重要度が表示される
- 検索トグル ON のときだけ検索が実行される
- トグル OFF のときは検索が行われない

