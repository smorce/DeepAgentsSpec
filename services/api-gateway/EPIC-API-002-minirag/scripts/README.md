# MiniRAG スクリプト使い方ガイド

このディレクトリには、MiniRAG サービスを起動・停止するためのスクリプトが含まれています。

## 前提条件

- Docker と Docker Compose がインストールされていること
- `.env` ファイルがプロジェクトルートに存在すること（必要な環境変数が設定されていること）

## スクリプト一覧

### `start.sh` - コンテナの起動

MiniRAG サービス（PostgreSQL + AGE + pgvector と MiniRAG API）を起動します。

#### 基本的な使い方

```bash
cd services/api-gateway/EPIC-API-002-minirag

# 通常起動
./scripts/start.sh

# DBをクリーンアップしてから起動（既存データを削除）。基本はこっち。
./scripts/start.sh cleanup
```

#### 動作内容

1. **通常起動モード** (`./scripts/start.sh`)
   - 既存のコンテナを起動（既に起動している場合は何もしない）
   - PostgreSQL コンテナのヘルスチェックが成功するまで待機（最大60秒）
   - `data/minirag` ディレクトリの権限を確認・修正
   - コンテナのログをリアルタイムで表示（Ctrl+C で終了、コンテナは停止しない）

2. **クリーンアップモード** (`./scripts/start.sh cleanup`)
   - 既存のコンテナ、ボリューム、イメージをすべて削除
   - `postgres/init` ディレクトリの権限を調整
   - 新しいコンテナを起動
   - 以降は通常起動モードと同じ

#### 注意事項

- スクリプト実行中に `Ctrl+C` を押すと、ログ表示のみが終了します（コンテナは停止しません）
- PostgreSQL のデータは Docker の named volume (`postgres_data`) に保存されます
- MiniRAG の作業ディレクトリは `./data/minirag` にマウントされます

---

### `stop.sh` - コンテナの停止

MiniRAG サービスを停止します。

#### 基本的な使い方

```bash
# 完全停止（データボリュームとイメージも削除）
./scripts/stop.sh

# データボリュームを保持して停止
./scripts/stop.sh keep-volumes

# データボリュームとイメージの両方を保持して停止
./scripts/stop.sh keep-all
```

#### 動作内容

1. **完全停止モード** (`./scripts/stop.sh`)
   - コンテナを停止・削除
   - データボリューム（`postgres_data`）を削除
   - Docker イメージを削除
   - **警告**: すべてのデータが失われます

2. **データ保持モード** (`./scripts/stop.sh keep-volumes`)
   - コンテナを停止・削除
   - データボリュームは保持（次回起動時にデータが残ります）
   - Docker イメージは削除

3. **完全保持モード** (`./scripts/stop.sh keep-all`)
   - コンテナを停止・削除
   - データボリュームとイメージの両方を保持
   - 次回起動時にイメージの再ビルドが不要

#### 使用例

```bash
# 開発中に一時的に停止（データは保持）
./scripts/stop.sh keep-volumes

# 次回起動時
./scripts/start.sh  # データが残っている状態で起動

# 完全にクリーンアップしたい場合
./scripts/stop.sh
# または
./scripts/start.sh cleanup
```

---

## サービスのアクセス情報

起動後、以下のエンドポイントにアクセスできます：

- **MiniRAG API**: http://localhost:8165
  - ヘルスチェック: http://localhost:8165/health
  - API ドキュメント: http://localhost:8165/docs (FastAPI の自動生成ドキュメント)

- **PostgreSQL**: localhost:5433
  - 接続情報は `.env` ファイルを参照してください

## トラブルシューティング

### コンテナが起動しない場合

```bash
# ログを確認
docker compose logs

# コンテナの状態を確認
docker compose ps

# 完全にクリーンアップして再起動
./scripts/stop.sh
./scripts/start.sh cleanup
```

### 権限エラーが発生する場合

Windows の WSL や Git Bash を使用している場合、`sudo` が必要な場合があります：

```bash
# sudo が必要な場合
sudo ./scripts/start.sh
```

### ポートが既に使用されている場合

```bash
# ポートの使用状況を確認
# Windows (PowerShell)
netstat -ano | findstr :8165
netstat -ano | findstr :5433

# Linux/WSL
lsof -i :8165
lsof -i :5433
```

既に使用されている場合は、該当プロセスを停止するか、`compose.yaml` でポート番号を変更してください。

## 関連ファイル

- `compose.yaml`: Docker Compose の設定ファイル
- `.env`: 環境変数の設定ファイル（プロジェクトルート）
- `minirag_app/`: MiniRAG アプリケーションのソースコード
- `postgres/`: PostgreSQL の初期化スクリプトとマイグレーション



MiniRAG API のテストイメージ
```
import time
import requests
from typing import List, Dict, Any, Optional

class MiniRAGClient:
    def __init__(self, base_url: str = "http://localhost:8165"):
        """
        MiniRAG API クライアント

        :param base_url: MiniRAG サーバーのベースURL
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }

    def bulk_register_documents(
        self,
        documents: List[Dict[str, Any]],
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        ドキュメントを一括登録する

        :param documents: documents 配列
        :param overwrite: 既存ドキュメントを上書きするか
        :return: APIレスポンス(JSON)
        """
        url = f"{self.base_url}/minirag/documents/bulk"
        payload = {
            "documents": documents,
            "overwrite": overwrite
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=3000
        )
        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        modes: Optional[List[str]] = None,
        top_k: int = 3,
        include_provenance: bool = True
    ) -> Dict[str, Any]:
        """
        ドキュメント検索を行う

        :param query: 検索クエリ
        :param modes: 検索モード（例: ["mini", "light"]）。指定しない場合は mini モード。
        :param top_k: 取得件数
        :param include_provenance: 出典情報を含めるか
        :return: APIレスポンス(JSON)
        """
        url = f"{self.base_url}/minirag/search"
        payload = {
            "query": query,
            "modes": modes or ["mini", "light"],
            "top_k": top_k,
            "include_provenance": include_provenance
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=3000
        )
        response.raise_for_status()
        return response.json()


client = MiniRAGClient(base_url="http://localhost:8165")

# 1.ドキュメント登録
documents = [
    {
        "workspace": "procurement_docs",
        "doc_id": "proc-plan-fy2026-apac-detailed",
        "title": "2026年度 APAC地域包括調達戦略・実施計画書（第1版）",
        "summary": "2026年度から2028年度までの中期経営計画に基づき、APAC地域における調達オペレーションの最適化、サプライヤー・レジリエンスの強化、およびコスト構造の改革を定義する包括的文書。",
        "body": ["""
# 1. はじめに
本計画書は、地政学的リスクの増大と原材料価格の変動に対応するため、2026年度におけるAPAC地域の調達方針を定めるものである。

# 2. 戦略目標
2026年度の最優先課題は「供給網の安定化」と「持続可能なコスト削減」の両立である。具体的には以下のKPIを設定する。
- 重点カテゴリーにおける複数社購買（Multi-sourcing）率を現状の40%から65%へ引き上げる。
- 地域内調達率（LCR: Local Content Ratio）を平均12%向上させ、物流コストと関税リスクを低減する。
- AIによる需給予測モデルを本格稼働させ、過剰在庫による保管コストを年間で約1.2億円削減する。

# 3. サプライヤーマネジメント
## 3.1 新規サプライヤーの開拓
東南アジア諸国（特にベトナム、タイ、インドネシア）における製造拠点の拡大に伴い、現地の有力サプライヤー50社との戦略的パートナーシップを締結する。
特にインド市場においては、半導体関連部材の現地調達比率を25%まで高めることを目指す。

## 3.2 ESG対応と監査
2026年度より、全ての主要サプライヤー（年間取引額1億円以上）に対し、CO2排出量の四半期報告を義務付ける。
また、人権デューデリジェンスに関する第三者機関による監査を、対象企業の30%で実施する。

# 4. デジタル変革（Procurement DX）
調達プロセスの透明性を高めるため、次世代型E-Procurementシステムを全拠点に導入する。
これにより、発注から支払いまでのリードタイムを20%短縮し、サプライヤー支払いの100%電子化を実現する。

# 5. リスク管理
地政学的リスクに対応するため、特定の1カ国に生産が集中している重要部材（23品目）について、代替生産拠点の確保をQ2（7-9月）までに完了させる。
大規模災害発生時の緊急調達フローを再構築し、初動対応時間を現状の24時間から6時間以内へ短縮する。"""
        ],
        "status": "published",
        "region": "APAC",
        "priority": 1,
        "metadata": {
            "department": "Strategic Procurement",
            "version": "1.0",
            "confidential_level": "Internal"
        }
    },
    {
        "workspace": "procurement_docs",
        "doc_id": "proc-it-service-policy-2026",
        "title": "2026年度 次世代ITサービス調達・運用ガイドライン",
        "summary": "グローバル全拠点におけるIT資産、ソフトウェア、クラウドサービスの調達基準とセキュリティ要件。",
        "body": ["""
# 1. 目的
本ガイドラインは、グループ全体のITガバナンスを強化し、サイバーセキュリティリスクを低減しつつ、ITコストの最適化を図ることを目的とする。

# 2. クラウドファースト戦略
新規ITシステムの導入に際しては、クラウドネイティブな構成を原則とする。
- 推奨プラットフォーム：AWS (Asia Pacific Regions), Microsoft Azure (Global)
- 調達基準：可用性99.99%以上の保証、およびISO 27017認証の取得が必須。

# 3. ソフトウェア・ライセンス管理
SaaS利用の急増に伴い、シャドーITの撲滅とライセンス費用の重複を排除する。
- 全拠点共通のSaaS管理ツールを導入し、利用率が30%以下のアプリケーションについては契約更新を行わない。
- オープンソースソフトウェア（OSS）の利用に関しては、法務部およびセキュリティ部門の承認が必要。

# 4. セキュリティ要件（サプライチェーンセキュリティ）
ITサービス提供ベンダーに対しては、以下のセキュリティ基準への準拠を求める。
1. SOC2 Type2レポートの定期的な提出。
2. ゼロトラストアーキテクチャに基づいたアクセス制御の実装。
3. 脆弱性診断を年2回以上実施し、その結果を報告すること。

# 5. ハードウェア調達と循環経済
PC、サーバー、ネットワーク機器の調達において、環境負荷を最小限に抑える。
- 廃棄されるハードウェアの80%以上をリサイクルまたはリユースする「IT資産循環プログラム」をQ3より開始する。
- 消費電力効率が前世代比で15%以上向上しているモデルを優先的に選定する。"""
        ],
        "status": "active",
        "region": "Global",
        "priority": 2,
        "metadata": {
            "department": "IT Management",
            "category": "IT",
            "type": "Policy"
        }
    }
]

print("=== 処理時間計測開始 ===\n")

# 2. ドキュメント登録の計測
print(f"1. ドキュメント登録中... (計 {len(documents)} 件)")
start_time = time.time()

try:
    register_result = client.bulk_register_documents(documents)
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"✅ 登録完了！ 処理時間: {elapsed:.2f} 秒")
    print(f"   サーバーレスポンス: {register_result}")

except Exception as e:
    print(f"❌ 登録中にエラーが発生しました: {e}")

print("\n" + "="*30 + "\n")

# 3. 検索処理の計測
queries = [
    "2026年度のインド市場における具体的な調達目標数値は何％ですか？",
    "ITサービス調達において必須とされる認証や可用性の基準は何ですか？",
    "サプライヤーに対して義務化される報告内容を教えてください。"
]

for i, q in enumerate(queries, 1):
    print(f"検索テスト {i}: 「{q}」")
    start_q = time.time()
    
    try:
        result = client.search(query=q, top_k=2)
        end_q = time.time()
        
        elapsed_q = end_q - start_q
        data = result.get('results', [{}])[0].get('answer', '回答なし')
        
        print(f"⏱️  検索時間: {elapsed_q:.2f} 秒")
        print("✅  回答内容")
        print(data['answer'])
        
        print("\n■ 関連キーワード（エンティティ）")
        for entity in data['provenance']['entities']:
            name = entity['entity_name']
            desc = entity['description']
            print(f"- {name}: {desc}")
        
        print("\n■ 参照元ドキュメント")
        for chunk in data['provenance']['chunks']:
            doc_id = chunk['full_doc_id']
            print(f"- ID: {doc_id}")

    except Exception as e:
        print(f"❌ 検索中にエラーが発生しました: {e}")
    
    print("-" * 20)
    print()
    print()

print("\n=== 全てのテストが完了しました ===")
```