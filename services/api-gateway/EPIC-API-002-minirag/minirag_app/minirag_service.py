from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModel, AutoTokenizer

from minirag import MiniRAG, QueryParam
from minirag.kg.postgres_impl import PostgreSQLDB
from minirag.llm.hf import hf_embed
from minirag.llm.openai import openai_complete_if_cache
from minirag.utils import EmbeddingFunc, locate_json_string_body_from_string

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-v3.2-speciale")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MINIRAG_WORKING_DIR = os.getenv("MINIRAG_WORKING_DIR", "/data/minirag")
MINIRAG_WORKSPACE = os.getenv("MINIRAG_WORKSPACE", "default")
AGE_GRAPH_NAME = os.getenv("AGE_GRAPH_NAME", "my_minirag_graph")
COSINE_THRESHOLD = float(os.getenv("COSINE_THRESHOLD", "0.4"))
STRUCTURED_TABLE = os.getenv("MINIRAG_STRUCTURED_TABLE", "public.structured_documents")

STRUCTURED_SCHEMA = {
    "table": STRUCTURED_TABLE,
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


class StructuredDocument(BaseModel):
    workspace: str
    doc_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str | List[str]] = None
    status: Optional[str] = None
    region: Optional[str] = None
    priority: Optional[int] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkInsertRequest(BaseModel):
    documents: List[StructuredDocument]
    overwrite: bool = True


class SearchRequest(BaseModel):
    query: str
    modes: List[str] = Field(default_factory=lambda: ["mini"])
    top_k: int = 3
    target_fields: Optional[List[str]] = None
    include_provenance: bool = True
    metadata_filter: Optional[Dict[str, Any]] = None


class DeleteResponse(BaseModel):
    deleted: int


async def openrouter_complete(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[Dict[str, str]]] = None,
    keyword_extraction: bool = False,
    **kwargs: Any,
) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    result = await openai_complete_if_cache(
        LLM_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        **kwargs,
    )
    if keyword_extraction:
        return locate_json_string_body_from_string(result)
    return result


def ensure_working_dir() -> None:
    os.makedirs(MINIRAG_WORKING_DIR, exist_ok=True)


def build_embedding_func() -> EmbeddingFunc:
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
    model = AutoModel.from_pretrained(EMBEDDING_MODEL)
    return EmbeddingFunc(
        embedding_dim=384,
        max_token_size=1000,
        func=lambda texts: hf_embed(texts, tokenizer=tokenizer, embed_model=model),
    )


async def ensure_structured_table(db: PostgreSQLDB) -> None:
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {STRUCTURED_TABLE} (
        workspace TEXT NOT NULL,
        doc_id TEXT NOT NULL,
        title TEXT,
        summary TEXT,
        body TEXT,
        status TEXT,
        region TEXT,
        priority INTEGER,
        created_at TIMESTAMP,
        PRIMARY KEY (workspace, doc_id)
    );
    """
    await db.execute(create_sql)


async def init_rag() -> tuple[MiniRAG, PostgreSQLDB]:
    ensure_working_dir()
    os.environ["AGE_GRAPH_NAME"] = AGE_GRAPH_NAME

    db_config = {
        "host": os.getenv("PGHOST", "postgres"),
        "port": int(os.getenv("PGPORT", "5432")),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "database": os.getenv("POSTGRES_DB"),
        "workspace": MINIRAG_WORKSPACE,
    }

    db_postgre = PostgreSQLDB(config=db_config)
    await db_postgre.initdb()
    await db_postgre.check_tables()
    await ensure_structured_table(db_postgre)

    rag = MiniRAG(
        working_dir=MINIRAG_WORKING_DIR,
        llm_model_func=openrouter_complete,
        llm_model_max_token_size=200,
        llm_model_name=LLM_MODEL,
        embedding_func=build_embedding_func(),
        kv_storage="PGKVStorage",
        vector_storage="PGVectorStorage",
        graph_storage="PGGraphStorage",
        doc_status_storage="PGDocStatusStorage",
        vector_db_storage_cls_kwargs={
            "cosine_better_than_threshold": COSINE_THRESHOLD,
        },
    )
    rag.set_storage_client(db_postgre)
    return rag, db_postgre


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        rag, db = await init_rag()
        app.state.rag = rag
        app.state.db = db
        yield
    finally:
        db = getattr(app.state, "db", None)
        if db and db.pool:
            await db.pool.close()


app = FastAPI(title="MiniRAG Service", lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/minirag/documents/bulk")
async def bulk_insert(request: BulkInsertRequest) -> Dict[str, Any]:
    if not request.documents:
        raise HTTPException(status_code=400, detail="documents must not be empty")

    rag: MiniRAG = app.state.rag
    docs = [doc.model_dump() for doc in request.documents]

    try:
        await rag.ainsert(
            docs,
            schema=STRUCTURED_SCHEMA,
            text_fields=["title", "summary", "body"],
            overwrite=request.overwrite,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"insert failed: {exc}") from exc

    return {"inserted": len(docs)}


@app.post("/minirag/search")
async def search(request: SearchRequest) -> Dict[str, Any]:
    rag: MiniRAG = app.state.rag

    async def run_mode(mode: str) -> Dict[str, Any]:
        param = QueryParam(
            mode=mode,
            top_k=request.top_k,
            target_fields=request.target_fields,
            include_provenance=request.include_provenance,
            metadata_filter=request.metadata_filter,
        )
        answer, sources = await rag.aquery(request.query, param=param)
        return {"mode": mode, "answer": answer, "sources": sources}

    try:
        results = await asyncio.gather(*[run_mode(mode) for mode in request.modes])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"search failed: {exc}") from exc

    total_sources = sum(len(result.get("sources") or []) for result in results)
    note = "0件" if total_sources == 0 else ""
    return {"query": request.query, "results": results, "note": note}


@app.delete("/minirag/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str, workspace: Optional[str] = None) -> DeleteResponse:
    rag: MiniRAG = app.state.rag
    db: PostgreSQLDB = app.state.db

    try:
        await rag._delete_existing_chunks([doc_id])
        if workspace:
            delete_sql = f"DELETE FROM {STRUCTURED_TABLE} WHERE workspace=$1 AND doc_id=$2"
            await db.execute(delete_sql, {"workspace": workspace, "doc_id": doc_id})
        else:
            delete_sql = f"DELETE FROM {STRUCTURED_TABLE} WHERE doc_id=$1"
            await db.execute(delete_sql, {"doc_id": doc_id})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"delete failed: {exc}") from exc

    return DeleteResponse(deleted=1)


@app.delete("/minirag/documents", response_model=DeleteResponse)
async def delete_documents_by_workspace(workspace: str) -> DeleteResponse:
    rag: MiniRAG = app.state.rag
    db: PostgreSQLDB = app.state.db

    try:
        rows = await db.query(
            f"SELECT doc_id FROM {STRUCTURED_TABLE} WHERE workspace=$1",
            params={"workspace": workspace},
            multirows=True,
        )
        doc_ids = [row["doc_id"] for row in rows]
        if doc_ids:
            await rag._delete_existing_chunks(doc_ids)
        await db.execute(
            f"DELETE FROM {STRUCTURED_TABLE} WHERE workspace=$1",
            {"workspace": workspace},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"delete failed: {exc}") from exc

    return DeleteResponse(deleted=len(doc_ids))

