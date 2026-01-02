from typing import List, Optional
from pydantic import BaseModel
from .base import StructuredDocument, SearchResult

class BulkRegisterRequest(BaseModel):
    workspace: str
    documents: List[StructuredDocument]

class BulkRegisterResponse(BaseModel):
    registered_count: int
    documents: List[StructuredDocument]

class SearchRequest(BaseModel):
    workspace: str
    query: str
    top_k: int = 5

class SearchResponse(BaseModel):
    count: int
    note: Optional[str] = None
    results: List[SearchResult]

class DeleteResponse(BaseModel):
    deleted_count: int
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    error_code: str
    message: str
