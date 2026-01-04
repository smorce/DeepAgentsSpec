from src.diary_service import _extract_search_items


def test_extract_search_items_prefers_sources_over_chunks():
    payload = {
        "results": [
            {
                "sources": [
                    {"doc_id": "doc-1", "summary": "SUMMARY", "body": "FULL BODY"}
                ],
                "answer": {
                    "provenance": {
                        "chunks": [
                            {"doc_id": "doc-1", "summary": "chunk", "body": "chunk body"}
                        ]
                    }
                },
            }
        ]
    }

    items = _extract_search_items(payload)

    assert items == [{"doc_id": "doc-1", "summary": "SUMMARY", "body": "FULL BODY"}]


def test_extract_search_items_uses_chunks_when_sources_missing():
    payload = {
        "results": [
            {
                "sources": [],
                "answer": {
                    "provenance": {
                        "chunks": [
                            {"doc_id": "doc-2", "summary": "chunk summary", "content": "chunk body"}
                        ]
                    }
                },
            }
        ]
    }

    items = _extract_search_items(payload)

    assert items == [{"doc_id": "doc-2", "summary": "chunk summary", "body": "chunk body"}]
