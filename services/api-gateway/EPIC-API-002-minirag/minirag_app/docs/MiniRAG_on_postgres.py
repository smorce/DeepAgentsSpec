# MiniRAG を postgres で実行する
# 必要なライブラリのインポート
import os
import tempfile
from minirag import MiniRAG, QueryParam
from minirag.llm.hf import (
    hf_model_complete,
    hf_embed,
)
# from minirag.llm.openai import openrouter_openai_complete
from minirag.llm.openai import openai_complete_if_cache
from minirag.utils import EmbeddingFunc
from minirag.utils import (
    wrap_embedding_func_with_attrs,
    locate_json_string_body_from_string,
    safe_unicode_decode,
    logger,
)

import asyncpg
from psycopg_pool import AsyncConnectionPool
from minirag.kg.postgres_impl import PostgreSQLDB
from minirag.kg.postgres_impl import PGKVStorage
from minirag.kg.postgres_impl import PGVectorStorage
from minirag.kg.postgres_impl import PGGraphStorage
from minirag.kg.postgres_impl import PGDocStatusStorage

from transformers import AutoModel, AutoTokenizer
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception
from openai import RateLimitError, APIStatusError # openaiライブラリが投げる例外をインポート
import asyncio
import warnings
warnings.filterwarnings('ignore')

# データベース接続テスト
import psycopg
from psycopg.rows import dict_row

def get_conn():
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg.connect(url, row_factory=dict_row)
    # fallback: assemble from separate vars
    dsn = (
        f"host={os.getenv('PGHOST','db')} "
        f"port={os.getenv('PGPORT','5432')} "
        f"dbname={os.getenv('PGDATABASE','postgres')} "
        f"user={os.getenv('POSTGRES_USER','postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD')}"
    )
    return psycopg.connect(dsn, row_factory=dict_row)

with get_conn() as conn, conn.cursor() as cur:
    cur.execute("SELECT version();")
    print(cur.fetchone())

def get_conn():
    """
    環境変数からデータベース接続情報を取得し、接続オブジェクトを返す。
    DATABASE_URLが設定されていればそれを使用し、なければ個別の変数を組み立てる。
    結果は辞書形式で返されるように設定済み。
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # DATABASE_URLが設定されている場合
        return psycopg.connect(url, row_factory=dict_row)
    
    # DATABASE_URLがない場合、個別の環境変数からDSNを組み立てる
    # PGPASSWORDが設定されていないと接続に失敗するため、チェックを追加するとより親切
    password = os.getenv('PGPASSWORD')
    if not password:
        raise ValueError("環境変数 PGPASSWORD が設定されていません。")
        
    dsn = (
        f"host={os.getenv('PGHOST', 'localhost')} "
        f"port={os.getenv('PGPORT', '5432')} "
        f"dbname={os.getenv('PGDATABASE', 'postgres')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={password}"
    )
    return psycopg.connect(dsn, row_factory=dict_row)

def find_recommended_products_for_alice(_results):
    """
    指定されたSQLクエリを実行し、'Alice'が好む商品とベクトル的に類似した商品を取得する。
    """
    # 実行したいSQLクエリを三重クォートで定義
    # これにより、複数行のクエリを読みやすく記述できる
    sql_query = """
    SELECT
        p.id,
        p.name,
        p.embedding
    FROM
        public.products AS p
    JOIN
        -- cypher関数でグラフクエリを実行し、結果をテーブルのように扱う
        cypher('my_minirag_graph', $$
            MATCH (u:User {name: 'Alice'})-[:LIKES]->(prod:Product)
            RETURN prod.product_id
        $$) AS liked(product_id agtype)
    ON
        -- グラフクエリの結果(agtype)を整数にキャストしてproductsテーブルのIDと結合
        p.id = (liked.product_id)::INTEGER
    ORDER BY
        -- pgvectorの<->演算子で、指定ベクトルとのコサイン距離が近い順に並び替え
        p.embedding <=> '[0.1, 0.1, 0.2]';
    """

    try:
        # with文で接続とカーソルを管理し、処理終了後に自動でクローズする
        with get_conn() as conn, conn.cursor() as cur:
            print("データベースに接続し、クエリを実行します...")
            
            # クエリの実行
            cur.execute(sql_query)
            
            # 全ての実行結果を取得 (fetchall)
            # 1件だけなら fetchone(), 複数件なら fetchall() を使う
            results = cur.fetchall()
            
            print("\n--- クエリ実行結果 ---")
            if results:
                # 取得した結果を1行ずつ表示
                for row in results:
                    print(row)
                    _results.append(row)
            else:
                print("条件に一致する結果は見つかりませんでした。")
        return _results

    except psycopg.Error as e:
        print(f"データベースエラーが発生しました: {e}")
    except ValueError as e:
        print(f"設定エラーが発生しました: {e}")

query_results = []
query_results = find_recommended_products_for_alice(query_results)

use_japanese_embedding = False

if use_japanese_embedding:
    # MINI モードでの回答ができなくなったので、逆に精度が落ちたかも。
    EMBEDDING_MODEL = "hotchpotch/static-embedding-japanese"
    EMBEDDING_DIM   = 1024
    TOKENIZER_MODEL = "hotchpotch/xlm-roberta-japanese-tokenizer"
    print("-------------- static-embedding-japanese を使用します --------------")
else:
    # 埋め込みモデルの設定
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM   = 384
    print("-------------- all-MiniLM-L6-v2 を使用します --------------")


# LLMの設定
LLM_MODEL = "deepseek/deepseek-v3.2-speciale"   # "qwen/qwen3-235b-a22b-2507"

# 作業ディレクトリの作成
WORKING_DIR = "/tmp/minirag_demo"
os.makedirs(WORKING_DIR, exist_ok=True)

print(f"作業ディレクトリ: {WORKING_DIR}")


# DATA_PATH = args.datapath
# QUERY_PATH = args.querypath
# OUTPUT_PATH = args.outputpath
# print("USING LLM:", LLM_MODEL)
# print("USING WORKING DIR:", WORKING_DIR)

if use_japanese_embedding:

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu", token=HF_TOKEN)
    
    query = "美味しいラーメン屋に行きたい"
    docs = [
        "素敵なカフェが近所にあるよ。落ち着いた雰囲気でゆっくりできるし、窓際の席からは公園の景色も見えるんだ。",
        "新鮮な魚介を提供する店です。地元の漁師から直接仕入れているので鮮度は抜群ですし、料理人の腕も確かです。",
        "あそこは行きにくいけど、隠れた豚骨の名店だよ。スープが最高だし、麺の硬さも好み。",
        "おすすめの中華そばの店を教えてあげる。とりわけチャーシューが手作りで柔らかくてジューシーなんだ。",
    ]
    
    embeddings = model.encode([query] + docs)
    print(embeddings.shape)
    similarities = model.similarity(embeddings[0], embeddings[1:])
    for i, similarity in enumerate(similarities[0].tolist()):
        print(f"{similarity:.04f}: {docs[i]}")

else:
    
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL, token=HF_TOKEN)
    model = AutoModel.from_pretrained(EMBEDDING_MODEL, token=HF_TOKEN)

# transformer の API で使えるように変換する
if use_japanese_embedding:
    
    import torch
    from torch import nn
    from transformers import PreTrainedModel, PretrainedConfig
    from transformers.modeling_outputs import BaseModelOutputWithPoolingAndCrossAttentions
    
    
    class StaticEmbeddingConfig(PretrainedConfig):
        model_type = "static-embedding"
    
        def __init__(self, vocab_size=32768, hidden_size=1024, pad_token_id=0, **kwargs):
            super().__init__(pad_token_id=pad_token_id, **kwargs)
            self.vocab_size = vocab_size
            self.hidden_size = hidden_size
    
    
    class StaticEmbeddingModel(PreTrainedModel):
        config_class = StaticEmbeddingConfig
    
        def __init__(self, config: StaticEmbeddingConfig):
            super().__init__(config)
            # ★ EmbeddingBag そのものでも OK ですが、
            #   シーケンス長をそろえて attention_mask で平均を取る方が扱いやすいので nn.Embedding に変更
            self.embedding = nn.Embedding(
                num_embeddings=config.vocab_size,
                embedding_dim=config.hidden_size,
                padding_idx=config.pad_token_id,
            )
            self.post_init()  # transformers の重み初期化
    
        def forward(self, input_ids, attention_mask=None, **kwargs):
            """
            - input_ids      : (batch, seq_len)
            - attention_mask : (batch, seq_len) — 0 は padding
            戻り値は Transformers 共通の BaseModelOutputWithPoolingAndCrossAttentions
            """
            if attention_mask is None:
                attention_mask = (input_ids != self.config.pad_token_id).int()
    
            token_embs = self.embedding(input_ids)                       # (B, L, H)
            # マスク付き平均プール
            masked_embs = token_embs * attention_mask.unsqueeze(-1)      # (B, L, H)
            lengths = attention_mask.sum(dim=1, keepdim=True).clamp(min=1e-8)  # (B, 1)
            sentence_emb = masked_embs.sum(dim=1) / lengths              # (B, H)
    
            return BaseModelOutputWithPoolingAndCrossAttentions(
                last_hidden_state=token_embs,  # ここでは token レベルをそのまま
                pooler_output=sentence_emb,    # 文ベクトル
                attentions=None,
                cross_attentions=None,
            )

if use_japanese_embedding:
    """
    SentenceTransformer 版 (hotchpotch/static-embedding-japanese) から
    StaticEmbeddingModel へ重みをコピーして保存するスクリプト
    """
    
    SRC = "hotchpotch/static-embedding-japanese"   # オリジナル
    DST = "./static-embedding-transformers"        # 保存先
    
    # ① SentenceTransformer を読み込む
    st_model = SentenceTransformer(SRC)
    embedding_weight = st_model[0].embedding.weight.data   # nn.EmbeddingBag の重みを取得
    
    # ② Config → Model を作成
    config = StaticEmbeddingConfig(
        vocab_size=embedding_weight.size(0),
        hidden_size=embedding_weight.size(1),
        pad_token_id=0,           # トークナイザの <pad> が id=0
    )
    model = StaticEmbeddingModel(config)
    
    # ③ 重みコピー
    with torch.no_grad():
        model.embedding.weight.copy_(embedding_weight)
    
    # ④ save_pretrained で書き出し
    model.save_pretrained(DST)
    # st_model.tokenizer.save_pretrained(DST)   # tokenizer.json なども一緒に保存
    
    print(f"✅ 変換完了 — 保存先: {DST}")

if use_japanese_embedding:
    
    MODEL_DIR = "./static-embedding-transformers"
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
    model     = StaticEmbeddingModel.from_pretrained(MODEL_DIR)
    
    sentences = [
        "美味しいラーメン屋に行きたい",
        "あそこは行きにくいけど、隠れた豚骨の名店だよ。スープが最高だし、麺の硬さも好み。",
    ]
    
    inputs = tokenizer(
        sentences,
        return_tensors="pt",
        padding=True,
        truncation=True,
        add_special_tokens=False,   # 元モデルは special tokens なし
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
        vecs = outputs.pooler_output     # (batch, hidden_size)
    
    print("shape:", vecs.shape)          # torch.Size([2, 1024])
    similarity = torch.nn.functional.cosine_similarity(vecs[0], vecs[1], dim=0)
    print("cosine:", similarity.item())

# どのエラーでリトライするかを定義
# 429 (RateLimitError) や サーバー側のエラー(5xx) でリトライするのが一般的
def should_retry(e: Exception) -> bool:
    if isinstance(e, RateLimitError):
        print(f"RateLimitError発生。リトライします...: {e}")
        return True
    # 5xx系のサーバーエラーでもリトライすることが多い
    if isinstance(e, APIStatusError) and e.status_code >= 500:
        print(f"サーバーエラー( {e.status_code} )発生。リトライします...: {e}")
        return True
    return False

@retry(
    wait=wait_random_exponential(multiplier=30, max=100), # 30, 32, 34, 38秒...とランダムな時間を加えて待つ（最大100秒）
    stop=stop_after_attempt(5), # 最大5回リトライする
    retry=retry_if_exception(should_retry) # 上で定義した条件の例外が発生した場合にリトライ
)
async def openrouter_openai_complete(
    prompt,
    system_prompt=None,
    history_messages=[],
    keyword_extraction=False,
    api_key: str = None,
    **kwargs,
) -> str:
    # if api_key:
    #     os.environ["OPENROUTER_API_KEY"] = api_key

    keyword_extraction = kwargs.pop("keyword_extraction", None)
    result = await openai_complete_if_cache(
        LLM_MODEL,  # change accordingly
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        **kwargs,
    )
    if keyword_extraction:  # TODO: use JSON API
        return locate_json_string_body_from_string(result)
    return result

# RAGシステムセットアップ
async def setup_rag_system():
    """RAGシステムを初期化し、準備ができたインスタンスを返す"""

    # 1. データベース設定
    db_config={
        "host": "postgres",    # これは Docker のサービス名「postgres」で指定
        "port": 5432,
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "database": os.getenv("POSTGRES_DB"),
    }

    # 2. PostgreSQLDBインスタンスを作成
    db_postgre = PostgreSQLDB(config=db_config)

    # 3. データベース接続を初期化
    print("------------------------- ポスグレに接続しています -------------------------")
    await db_postgre.initdb()
    print("------------------------- ポスグレに接続しました！ -------------------------")

    # 必要なテーブルが存在するかチェックし、なければ作成する
    print("------------------------- テーブルの存在を確認・作成しています -------------------------")
    await db_postgre.check_tables()
    print("------------------------- テーブルの準備が完了しました！ -------------------------")

    # 5. MiniRAGインスタンスを作成
    os.environ["AGE_GRAPH_NAME"] = "my_minirag_graph" # init_db.sh で指定したもの
    rag = MiniRAG(
        working_dir=WORKING_DIR,
        # llm_model_func=hf_model_complete,
        # llm_model_func=gemini_2_5_flash_complete,
        llm_model_func=openrouter_openai_complete,
        llm_model_max_token_size=200,
        llm_model_name=LLM_MODEL,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            max_token_size=1000,
            func=lambda texts: hf_embed(
                texts,
                tokenizer=tokenizer,
                embed_model=model
            ),
        ),
        kv_storage="PGKVStorage",
        vector_storage="PGVectorStorage",
        graph_storage="PGGraphStorage",
        doc_status_storage="PGDocStatusStorage",
        vector_db_storage_cls_kwargs={
            "cosine_better_than_threshold": float(os.getenv("COSINE_THRESHOLD"))
        }
    )
    # データベースの情報を渡す
    rag.set_storage_client(db_postgre)    
    return rag

# RAGシステムをセットアップ
try:
    rag = await setup_rag_system()
    print("------------------------- MiniRAGが初期化されました！ -------------------------")
except Exception as e:
    print(f"RAGシステムのセットアップに失敗しました: {e}")

# 構造化ドキュメントのマルチフィールド挿入と検索
from datetime import datetime, timezone

workspace = rag.storage_client.workspace

structured_docs = [
    {
        "workspace": "procurement_docs",
        "doc_id": "proc-plan-fy2026-apac",
        "title": "2026年度 APAC地域向けノートPC調達計画書 第2版",
        "summary": "2026年度に従業員向けに配布するノートPC（約5,000台）の調達に関する戦略、タイムライン、および予算の概要。本計画は、コスト効率の最適化とサプライチェーンの安定化を目的とする。",
        "body": [
            "## 1. 計画概要\n- **目的**: TCO（総所有コスト）の15%削減と、主要サプライヤーとのパートナーシップ強化。\n- **対象地域**: 日本、シンガポール、オーストラリア、インド。\n- **想定予算**: 750万ドル。",
            "## 2. 実行フェーズ\n- **フェーズ1 (2025/Q4)**: 各拠点からの要求仕様の集約、RFP（提案依頼書）の作成と候補ベンダー（3社）への送付。\n- **フェーズ2 (2026/Q1)**: ベンダーからの提案評価、価格およびサポート条件の交渉、実機評価。\n- **フェーズ3 (2026/Q2)**: 最終サプライヤーの選定、契約締結、および初期ロットの発注。",
            "## 3. リスク管理\n- **地政学的リスク**: 特定国への依存を避けるため、サプライヤーの生産拠点を分散させる。\n- **為替変動リスク**: 主要通貨（USD, JPY, SGD）での価格固定を交渉条件に含める。",
        ],
        "status": "in_progress",
        "region": "APAC",
        "priority": 1,
        "created_at": datetime(2025, 10, 1, 8, 30, tzinfo=timezone.utc),
        "metadata": {
            "category": "planning_document",
            "region": "APAC",
            "year": 2026,
            "owner_department": "IT Procurement Department",
            "approver": "John Smith",
            "version": "2.1"
        },
    },
    {
        "workspace": "procurement_docs",
        "doc_id": "contract-na-fy2025-qsi",
        "title": "【署名済】北米市場向けサプライヤー契約書 (Quantum Systems Inc.)",
        "summary": "北米（アメリカ、カナダ）市場におけるノートPCの独占的サプライヤーとして『Quantum Systems Inc.』と締結した供給契約。本契約は、納期、価格、およびサービスレベルアグリーメント（SLA）を規定する。",
        "body": [
            "## 契約の主な条件\n- **契約番号**: CTR-NA-2025-0012\n- **契約期間**: 2025年1月1日～2025年12月31日\n- **対象製品**: 法人向けノートPC『QuantumBook Pro X5』および『QuantumBook Air M3』。",
            "## 価格と支払い条件\n- **単価**: ボリュームディスカウント適用後、1台あたり平均1,250ドル。\n- **支払いサイト**: 請求書受領後、60日以内（Net 60）。",
            "## サービスレベルアグリーメント (SLA)\n- **納期**: 発注確認後、21営業日以内に指定倉庫へ納品。\n- **ハードウェアサポート**: 故障発生時、翌営業日オンサイト修理対応。",
        ],
        "status": "finalized",
        "region": "NA",
        "priority": 1,
        "created_at": datetime(2025, 10, 2, 9, 15, tzinfo=timezone.utc),
        "metadata": {
            "category": "contract",
            "region": "NA",
            "year": 2025,
            "owner_department": "Legal & Supply Chain Management",
            "supplier_name": "Quantum Systems Inc.",
            "contract_value_usd": 12000000
        },
    },
]

schema = {
    "table": "public.customer_orders",
    "id_column": "doc_id",
    "fields": {
        "workspace": {"type": "text", "nullable": False},
        "doc_id": {"type": "text", "nullable": False},
        "title": {"type": "text"},
        "summary": {"type": "text"},
        "body": {"type": "text"},
        "status": {"type": "text"},
        "region": {"type": "text"},
        "priority": {"type": "integer"},
        "created_at": {"type": "timestamp"},
    },
    "conflict_columns": ["workspace", "doc_id"],
}

await rag.ainsert(structured_docs, schema=schema, text_fields=["title", "summary", "body"])
print(f"構造化ドキュメントを {len(structured_docs)} 件登録しました (workspace={workspace}).")

import json

doc_ids = [doc["doc_id"] for doc in structured_docs]
chunk_rows = await rag.storage_client.query(
    """
    SELECT full_doc_id,
           metadata,
           metadata->>'text_field' AS text_field,
           content,
           chunk_order_index
    FROM LIGHTRAG_DOC_CHUNKS
    WHERE workspace=$1
      AND full_doc_id = ANY($2::text[])
    ORDER BY full_doc_id, chunk_order_index
    """,
    params={"workspace": workspace, "doc_ids": doc_ids},
    multirows=True,
)

print(f"取得チャンク数: {len(chunk_rows)}")
for row in chunk_rows:
    head = row["content"].split("\n")[0][:60]
    metadata_json = json.dumps(row["metadata"], ensure_ascii=False)
    print(f"- {row['full_doc_id']} | text_field={row['text_field']} | chunk_order={row['chunk_order_index']}\n  preview: {head}\n  metadata: {metadata_json}")


# ここからが検索例。モードが ["naive", "mini", "light"] 3つあるので、それぞれ検索して検索結果を統合するようにしてください。検索は並列化すること。
# target_fields を利用した検索例
from pprint import pprint

summary_param = QueryParam(
    mode="light",
    target_fields=["summary"],
    include_provenance=True,
    top_k=3,
)
summary_result, summary_sources = await rag.aquery(
    "調達計画の概要を教えてください。",
    param=summary_param,
)

print("回答:")
if isinstance(summary_result, dict):
    pprint(summary_result)
else:
    print(summary_result)

print("\n参照したチャンク:")
for src in summary_sources:
    print("-", src.split("\n")[0])

# target_fields と metadata_filter の併用
supply_param = QueryParam(
    mode="light",
    target_fields=["body"],
    metadata_filter={"category": "supply", "year": 2025},
    include_provenance=True,
    only_need_context=True,
    top_k=3,
)
supply_context, supply_sources = await rag.aquery(
    "北米サプライ契約の詳細を教えてください。",
    param=supply_param,
)

print("取得したコンテキスト:")
if isinstance(supply_context, dict):
    pprint(supply_context)
else:
    print(supply_context)

print("\n対象チャンク (body フィールド):")
for src in supply_sources:
    print("-", src.split("\n")[0])

# 時間フィルタ（start_time / end_time）の利用
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)

param = QueryParam(
    mode="light",
    start_time=now.isoformat(),
    end_time=(now + timedelta(hours=1)).isoformat(),
    metadata_filter={"category": "plan"},
)

answer, sources = await rag.aquery("最近登録された計画について教えて", param=param)
print(answer)
print(sources)

# target_fields を指定しない場合（_all チャンク）
default_param = QueryParam(mode="light", top_k=3)
default_answer, default_sources = await rag.aquery(
    "契約全体の概要をまとめてください。",
    param=default_param,
)

print("回答:")
print(default_answer)

print("\n参照したソース: ")
for src in default_sources:
    print(src)
    print("================================================")