from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Optional
import os
import logging
from src.minirag.schemas import (
    BulkRegisterRequest, BulkRegisterResponse,
    SearchRequest, SearchResponse,
    DeleteResponse, ErrorResponse
)
from src.minirag.base import MiniRAGService
from src.minirag.service import InMemoryMiniRAGService
from src.minirag.postgres_service import PostgresMiniRAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/minirag", tags=["minirag"])

# Singleton instance
_service = None

async def get_service() -> MiniRAGService:
    global _service
    if _service is None:
        storage_type = os.environ.get("MINIRAG_STORAGE_TYPE", "memory").lower()
        if storage_type == "postgres":
            logger.info("Initializing PostgresMiniRAGService")
            _service = PostgresMiniRAGService()
        else:
            logger.info("Initializing InMemoryMiniRAGService")
            _service = InMemoryMiniRAGService()
    return _service

async def verify_api_key(x_demo_api_key: str = Header(...)):
    if not x_demo_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    # For demo, accept any non-empty key or specific one if needed
    return x_demo_api_key

@router.post("/documents/bulk", response_model=BulkRegisterResponse)
async def bulk_register(
    req: BulkRegisterRequest,
    service: MiniRAGService = Depends(get_service),
    api_key: str = Depends(verify_api_key)
):
    count = await service.bulk_register(req.workspace, req.documents)
    return BulkRegisterResponse(registered_count=count, documents=req.documents)

@router.post("/search", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    service: MiniRAGService = Depends(get_service),
    api_key: str = Depends(verify_api_key)
):
    results = await service.search(req.workspace, req.query, req.top_k)
    note = "0件" if len(results) == 0 else None
    return SearchResponse(count=len(results), results=results, note=note)

@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_one(
    doc_id: str,
    workspace: str = Query(...),
    service: MiniRAGService = Depends(get_service),
    api_key: str = Depends(verify_api_key)
):
    count = await service.delete_one(workspace, doc_id)
    return DeleteResponse(deleted_count=count, message="Document deleted" if count > 0 else "Document not found")

@router.delete("/documents", response_model=DeleteResponse)
async def delete_all(
    workspace: str = Query(...),
    service: MiniRAGService = Depends(get_service),
    api_key: str = Depends(verify_api_key)
):
    count = await service.delete_all(workspace)
    return DeleteResponse(deleted_count=count, message=f"All documents in workspace '{workspace}' deleted")
