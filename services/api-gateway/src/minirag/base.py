from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class StructuredDocument(BaseModel):
    workspace: str
    doc_id: str
    title: str
    summary: str
    body: str
    status: str
    region: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    doc_id: str
    title: str
    summary: str
    relevance: float
    source_fields: Optional[List[str]] = None

class MiniRAGService:
    async def bulk_register(self, workspace: str, documents: List[StructuredDocument]) -> int:
        raise NotImplementedError

    async def search(self, workspace: str, query: str, top_k: int = 5) -> List[SearchResult]:
        raise NotImplementedError

    async def delete_one(self, workspace: str, doc_id: str) -> int:
        raise NotImplementedError

    async def delete_all(self, workspace: str) -> int:
        raise NotImplementedError
