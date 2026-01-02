# Research: F-API-003 MiniRAGデモ用チャットUI

## Decision 1: UI 実装は avatar-ui の Vite/Electron クライアントに配置
- Decision: `services/avatar-ui/app/src/renderer` 配下に MiniRAG デモ UI を実装する
- Rationale: 既存の UI サービス構成（Vite/Electron）と整合し、追加サービスを不要にできる
- Alternatives considered:
  - 新規 UI サービスを追加（デモ用途には過剰）

## Decision 2: API 連携は REST JSON + 固定デモ API キー
- Decision: F-API-002 の REST エンドポイントを直接呼び、`X-Demo-Api-Key` を埋め込む
- Rationale: デモ用途で最小限の安全性と実装コストのバランスが良い
- Alternatives considered:
  - UI にキー入力欄を設ける（操作の簡潔さが下がる）
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
