from typing import List, Dict
from datetime import datetime
from .base import MiniRAGService, StructuredDocument, SearchResult

class InMemoryMiniRAGService(MiniRAGService):
    def __init__(self):
        # Key: (workspace, doc_id), Value: StructuredDocument
        self._store: Dict[tuple[str, str], StructuredDocument] = {}

    async def bulk_register(self, workspace: str, documents: List[StructuredDocument]) -> int:
        count = 0
        for doc in documents:
            key = (workspace, doc.doc_id)
            self._store[key] = doc
            count += 1
        return count

    async def search(self, workspace: str, query: str, top_k: int = 5) -> List[SearchResult]:
        results = []
        query_lower = query.lower()

        # Simple keyword matching for demo purposes
        for (ws, doc_id), doc in self._store.items():
            if ws != workspace:
                continue

            score = 0.0
            if query_lower in doc.title.lower():
                score += 0.5
            if query_lower in doc.summary.lower():
                score += 0.3
            if query_lower in doc.body.lower():
                score += 0.2

            if score > 0:
                results.append(SearchResult(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    summary=doc.summary,
                    relevance=score,
                    source_fields=["title", "summary", "body"]
                ))

        # Sort by relevance desc
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:top_k]

    async def delete_one(self, workspace: str, doc_id: str) -> int:
        key = (workspace, doc_id)
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    async def delete_all(self, workspace: str) -> int:
        keys_to_delete = [k for k in self._store.keys() if k[0] == workspace]
        count = len(keys_to_delete)
        for k in keys_to_delete:
            del self._store[k]
        return count
