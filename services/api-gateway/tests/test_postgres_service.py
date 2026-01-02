import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from src.minirag.postgres_service import PostgresMiniRAGService
from src.minirag.schemas import StructuredDocument, SearchResult
import numpy as np

# Mocking asyncpg
@pytest.fixture
def mock_pool():
    pool = MagicMock() # pool itself is synchronous object that returns context manager
    # Context manager for acquire
    conn = AsyncMock()
    # pool.acquire() returns an async context manager
    acquire_ctx = AsyncMock()
    acquire_ctx.__aenter__.return_value = conn
    pool.acquire.return_value = acquire_ctx
    return pool, conn

@pytest.mark.asyncio
async def test_postgres_init_db(mock_pool):
    pool, conn = mock_pool

    # asyncpg.create_pool is an async function (or returns an awaitable)
    # We need to mock it so that awaiting it returns our mock_pool object

    # Create an AsyncMock for create_pool that returns the mock_pool when awaited
    async_create_pool = AsyncMock(return_value=pool)

    with patch("asyncpg.create_pool", side_effect=async_create_pool) as create_pool_mock:
        service = PostgresMiniRAGService(db_url="postgresql://user:pass@localhost/db")
        # Pre-set pool to avoid connect() creating a new one if we want strict control,
        # but here we test the flow including connect()
        service._pool = None

        await service.init_db()

        # Verify connect called create_pool
        create_pool_mock.assert_called_once()

        # Verify extension and table creation
        assert conn.execute.call_count == 2
        args_list = conn.execute.call_args_list
        assert "CREATE EXTENSION" in args_list[0][0][0]
        assert "CREATE TABLE" in args_list[1][0][0]

@pytest.mark.asyncio
async def test_postgres_bulk_register(mock_pool):
    pool, conn = mock_pool
    service = PostgresMiniRAGService(db_url="mock://")
    service._pool = pool # Inject mock pool

    docs = [
        StructuredDocument(
            workspace="ws", doc_id="1", title="T", summary="S", body="B",
            status="ok", created_at=datetime.now()
        )
    ]

    await service.bulk_register("ws", docs)

    conn.executemany.assert_called_once()
    args = conn.executemany.call_args[0]
    sql = args[0]
    records = args[1]

    assert "INSERT INTO minirag_documents" in sql
    assert len(records) == 1
    # Check if embedding was added (mock embedding func returns np array, we convert to list)
    assert isinstance(records[0][-1], list)

@pytest.mark.asyncio
async def test_postgres_search(mock_pool):
    pool, conn = mock_pool
    service = PostgresMiniRAGService(db_url="mock://")
    service._pool = pool

    # Mock search result
    conn.fetch.return_value = [
        {
            "doc_id": "1",
            "title": "Title",
            "summary": "Summary",
            "relevance": 0.95
        }
    ]

    results = await service.search("ws", "query")

    conn.fetch.assert_called_once()
    assert len(results) == 1
    assert results[0].doc_id == "1"
    assert results[0].relevance == 0.95

@pytest.mark.asyncio
async def test_postgres_delete_one(mock_pool):
    pool, conn = mock_pool
    service = PostgresMiniRAGService(db_url="mock://")
    service._pool = pool

    conn.execute.return_value = "DELETE 1"

    count = await service.delete_one("ws", "1")

    conn.execute.assert_called_once()
    assert "DELETE FROM minirag_documents" in conn.execute.call_args[0][0]
    assert count == 1
