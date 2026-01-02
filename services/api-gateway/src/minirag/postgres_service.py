import os
import json
import logging
import asyncio
import numpy as np
import asyncpg
from typing import List, Optional, Any
from .base import MiniRAGService, StructuredDocument, SearchResult
from .utils import EmbeddingFunc, compute_mdhash_id

logger = logging.getLogger(__name__)

class PostgresMiniRAGService(MiniRAGService):
    def __init__(self, db_url: str = None, embedding_func: EmbeddingFunc = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        self.embedding_func = embedding_func or EmbeddingFunc(
            embedding_dim=384,
            max_token_size=8192,
            func=self._mock_embed
        )
        self.table_name = "minirag_documents"
        self._pool = None

    async def _mock_embed(self, texts: List[str]) -> np.ndarray:
        return np.random.rand(len(texts), self.embedding_func.embedding_dim)

    async def connect(self):
        if self._pool is None:
            logger.info(f"Connecting to Postgres: {self.db_url}")
            self._pool = await asyncpg.create_pool(dsn=self.db_url)

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def init_db(self):
        """Initialize table and pgvector extension"""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    workspace TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT,
                    region TEXT,
                    priority INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB,
                    embedding vector({self.embedding_func.embedding_dim}),
                    PRIMARY KEY (workspace, doc_id)
                );
            """)

    async def bulk_register(self, workspace: str, documents: List[StructuredDocument]) -> int:
        if not documents:
            return 0
        if not self._pool:
            await self.connect()

        texts_to_embed = [
            f"{doc.title}\n{doc.summary}\n{doc.body}" for doc in documents
        ]
        embeddings = await self.embedding_func(texts_to_embed)

        records = []
        for doc, emb in zip(documents, embeddings):
            records.append((
                workspace,
                doc.doc_id,
                doc.title,
                doc.summary,
                doc.body,
                doc.status,
                doc.region,
                doc.priority,
                doc.created_at,
                json.dumps(doc.metadata) if doc.metadata else None,
                emb.tolist()
            ))

        query = f"""
            INSERT INTO {self.table_name}
            (workspace, doc_id, title, summary, body, status, region, priority, created_at, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (workspace, doc_id) DO UPDATE SET
                title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                body = EXCLUDED.body,
                status = EXCLUDED.status,
                region = EXCLUDED.region,
                priority = EXCLUDED.priority,
                created_at = EXCLUDED.created_at,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding;
        """

        async with self._pool.acquire() as conn:
            await conn.executemany(query, records)

        return len(documents)

    async def search(self, workspace: str, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self._pool:
            await self.connect()

        query_embedding_np = await self.embedding_func([query])
        query_embedding = query_embedding_np[0].tolist()

        sql = f"""
            SELECT doc_id, title, summary, 1 - (embedding <=> $2) as relevance
            FROM {self.table_name}
            WHERE workspace = $1
            ORDER BY embedding <=> $2
            LIMIT $3;
        """

        results = []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, workspace, query_embedding, top_k)
            for row in rows:
                results.append(SearchResult(
                    doc_id=row['doc_id'],
                    title=row['title'],
                    summary=row['summary'],
                    relevance=row['relevance'],
                    source_fields=["title", "summary", "body"]
                ))
        return results

    async def delete_one(self, workspace: str, doc_id: str) -> int:
        if not self._pool:
            await self.connect()

        sql = f"DELETE FROM {self.table_name} WHERE workspace = $1 AND doc_id = $2"
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, workspace, doc_id)
            return int(result.split(" ")[1])

    async def delete_all(self, workspace: str) -> int:
        if not self._pool:
            await self.connect()

        sql = f"DELETE FROM {self.table_name} WHERE workspace = $1"
        async with self._pool.acquire() as conn:
            result = await conn.execute(sql, workspace)
            return int(result.split(" ")[1])
