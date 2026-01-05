# Research: F-API-003 MiniRAGデモ用チャットUI

## Decision 1: UI 実装は静的HTML/JSで提供
- Decision: `services/minirag/EPIC-API-001-minirag-demo-ui/frontend/public/` に HTML/CSS/JS を配置する
- Rationale: ビルドなしで最小のHTTPサーバー配信を実現し、デモ用途に適した最小構成になる
- Alternatives considered:
  - Vite/Electron（avatar-ui を流用）※採用せず
  - 新規SPAフレームワーク導入（デモ用途には過剰）

## Decision 2: API 連携は REST JSON + 固定デモ API キー
- Decision: F-API-002 の REST エンドポイントを直接呼び、`X-Demo-Api-Key` を埋め込む
- Rationale: デモ用途で最小限の安全性と実装コストのバランスが良い
- Alternatives considered:
  - UI にキー入力欄を設ける（操作が複雑）
  - 認証なし（誤操作リスク）

## Decision 3: 操作モデル
- Decision: 検索はチャット入力、登録/削除はボタン操作
- Rationale: 誤操作を減らし、デモの導線を短く保てる
- Alternatives considered:
  - 全操作をチャットコマンドで行う（入力ミスが増える）
  - 全操作をフォームで行う（チャット体験が薄れる）

## Decision 4: 結果表示
- Decision: 検索結果は上位5件を関連度順で表示し、エラーはチャット履歴内に表示する
- Rationale: デモの理解を妨げず、UI 実装も簡潔
- Alternatives considered:
  - モーダルやバナーのみで通知（文脈が途切れやすい）
