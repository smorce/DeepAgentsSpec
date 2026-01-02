import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.minirag.schemas import BulkRegisterRequest, StructuredDocument
from datetime import datetime

client = TestClient(app)

API_KEY = "demo-key"
HEADERS = {"X-Demo-Api-Key": API_KEY}
WORKSPACE = "test-ws"

@pytest.fixture(autouse=True)
def clean_store():
    # Helper to clean store between tests if needed,
    # but since InMemoryMiniRAGService is a singleton in main,
    # we might need to rely on delete_all API or re-instantiate.
    # For now, we will rely on delete_all API.
    client.delete(f"/minirag/documents?workspace={WORKSPACE}", headers=HEADERS)

def test_bulk_register_and_search():
    # 1. Register
    docs = [
        StructuredDocument(
            workspace=WORKSPACE,
            doc_id="doc1",
            title="Test Doc One",
            summary="Summary of doc one",
            body="This is the body of document one.",
            status="active",
            created_at=datetime.now()
        ),
        StructuredDocument(
            workspace=WORKSPACE,
            doc_id="doc2",
            title="Test Doc Two",
            summary="Summary of doc two",
            body="This is the body of document two which mentions apple.",
            status="active",
            created_at=datetime.now()
        )
    ]

    # Convert Pydantic models to dicts for JSON serialization with datetime handling if needed
    # TestClient/httpx handles this but datetime might need isoformat string if manual dict
    payload = {
        "workspace": WORKSPACE,
        "documents": [doc.model_dump(mode="json") for doc in docs]
    }

    response = client.post("/minirag/documents/bulk", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["registered_count"] == 2

    # 2. Search Hit
    search_payload = {
        "workspace": WORKSPACE,
        "query": "apple"
    }
    response = client.post("/minirag/search", json=search_payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["doc_id"] == "doc2"

    # 3. Search Miss
    search_payload_miss = {
        "workspace": WORKSPACE,
        "query": "banana"
    }
    response = client.post("/minirag/search", json=search_payload_miss, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["note"] == "0件"

def test_delete_one():
    # Register one
    docs = [
        StructuredDocument(
            workspace=WORKSPACE,
            doc_id="doc-del",
            title="To be deleted",
            summary="...",
            body="...",
            status="active",
            created_at=datetime.now()
        )
    ]
    payload = {
        "workspace": WORKSPACE,
        "documents": [doc.model_dump(mode="json") for doc in docs]
    }
    client.post("/minirag/documents/bulk", json=payload, headers=HEADERS)

    # Delete it
    response = client.delete(f"/minirag/documents/doc-del?workspace={WORKSPACE}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1

    # Verify gone
    response = client.post("/minirag/search", json={"workspace": WORKSPACE, "query": "deleted"}, headers=HEADERS)
    assert response.json()["count"] == 0

def test_unauthorized():
    # If using Depends(verify_api_key), missing header typically raises 422 if it's considered a required field validation error by FastAPI/Pydantic,
    # or 401 if explicitly raised.
    # However, verify_api_key uses Header(...) which makes it required.
    # FastAPI usually returns 422 for missing required params.
    # But let's check what verify_api_key raises.
    # It raises 401 if not x_demo_api_key (empty string), but if header is MISSING, FastAPI validation kicks in first -> 422.
    # To test 401, we should send an empty key or invalid key if we had logic for that.
    # Our verify_api_key: `if not x_demo_api_key: raise 401`.

    # Case 1: Header missing -> 422 (FastAPI default for required header)
    response = client.post("/minirag/search", json={"workspace": "x", "query": "y"})
    assert response.status_code == 422

    # Case 2: Header present but empty -> 401 (Our logic)
    response = client.post("/minirag/search", json={"workspace": "x", "query": "y"}, headers={"X-Demo-Api-Key": ""})
    assert response.status_code == 401
