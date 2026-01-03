import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from google import genai

from src import config
from src.minirag_client import MiniRagClient, MiniRagConfig, MiniRagError


logger = logging.getLogger(__name__)


class DiaryValidationError(ValueError):
    pass


class DiaryAnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchSettings:
    enabled: bool
    top_k: int
    modes: tuple[str, ...]


@dataclass(frozen=True)
class DiaryAnalysis:
    title: str
    importance_score: int
    summary: str
    semantic_memory: str
    episodic_memory: str


_MINIRAG_CLIENT = MiniRagClient(
    MiniRagConfig(
        base_url=config.MINIRAG_BASE_URL,
        workspace=config.MINIRAG_WORKSPACE,
        timeout_seconds=config.MINIRAG_TIMEOUT_SECONDS,
    )
)

_search_settings_by_thread: dict[str, SearchSettings] = {}


def get_search_settings(thread_id: str) -> SearchSettings:
    return _search_settings_by_thread.get(
        thread_id,
        SearchSettings(
            enabled=config.MINIRAG_SEARCH_ENABLED_DEFAULT,
            top_k=config.MINIRAG_TOP_K_DEFAULT,
            modes=tuple(config.MINIRAG_SEARCH_MODES_DEFAULT),
        ),
    )


def set_search_settings(thread_id: str, settings: SearchSettings) -> SearchSettings:
    allowed_modes = set(config.MINIRAG_SEARCH_MODES_ALLOWED)
    normalized_modes: list[str] = []
    for mode in settings.modes:
        if mode not in allowed_modes:
            continue
        if mode in normalized_modes:
            continue
        normalized_modes.append(mode)
        if len(normalized_modes) >= 3:
            break
    clamped = SearchSettings(
        enabled=settings.enabled,
        top_k=max(1, min(settings.top_k, 10)),
        modes=tuple(normalized_modes),
    )
    _search_settings_by_thread[thread_id] = clamped
    return clamped


def format_transcript(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant" if role == "assistant" else "System"
        lines.append(f"{label}: {content}")
    return "\n".join(lines)


def build_analysis_prompt(messages: list[dict[str, Any]]) -> str:
    transcript = format_transcript(messages)
    return (
        "あなたは日記会話を整理するアシスタントです。"
        "以下の会話から日記タイトル、重要度(1-10)、サマリー、"
        "セマンティック記憶、エピソード記憶を抽出してください。"
        "必ず JSON のみを返し、キーは次の通りにすること:\n"
        "title, importance_score, summary, semantic_memory, episodic_memory\n\n"
        "会話:\n"
        f"{transcript}"
    )


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    candidates = getattr(response, "candidates", None)
    if candidates:
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts and hasattr(parts[0], "text"):
            return parts[0].text
    return ""


def _extract_json_payload(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise DiaryAnalysisError("Gemini response did not include JSON payload.")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise DiaryAnalysisError(f"Failed to parse JSON payload: {exc}") from exc


async def analyze_diary(messages: list[dict[str, Any]]) -> DiaryAnalysis:
    if not messages:
        raise DiaryValidationError("No messages provided for diary analysis.")
    prompt = build_analysis_prompt(messages)
    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=config.LLM_MODEL,
        contents=prompt,
    )
    text = _extract_response_text(response)
    if not text:
        raise DiaryAnalysisError("Gemini response was empty.")
    payload = _extract_json_payload(text)
    try:
        importance_score = int(payload["importance_score"])
    except (KeyError, ValueError, TypeError) as exc:
        raise DiaryAnalysisError("importance_score is missing or invalid.") from exc
    return DiaryAnalysis(
        title=str(payload.get("title", "")).strip(),
        importance_score=importance_score,
        summary=str(payload.get("summary", "")).strip(),
        semantic_memory=str(payload.get("semantic_memory", "")).strip(),
        episodic_memory=str(payload.get("episodic_memory", "")).strip(),
    )


def _generate_doc_id(now: datetime) -> str:
    short_id = uuid.uuid4().hex[:8]
    return f"journal-{now.strftime('%Y%m%d-%H%M%S')}-{short_id}"


def build_diary_document(
    *,
    messages: list[dict[str, Any]],
    analysis: DiaryAnalysis,
    thread_id: str,
    search_settings: SearchSettings,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    transcript = format_transcript(messages)
    body = "\n\n".join(
        [
            "## Conversation",
            transcript,
            "## Semantic Memory",
            analysis.semantic_memory,
            "## Episodic Memory",
            analysis.episodic_memory,
        ]
    )
    return {
        "workspace": config.MINIRAG_WORKSPACE,
        "doc_id": _generate_doc_id(now),
        "title": analysis.title,
        "summary": analysis.summary,
        "body": body,
        "importance_score": analysis.importance_score,
        "semantic_memory": analysis.semantic_memory,
        "episodic_memory": analysis.episodic_memory,
        "created_at": now.isoformat(),
        "metadata": {
            "model": config.LLM_MODEL,
            "message_count": len(messages),
            "search_enabled": search_settings.enabled,
            "top_k": search_settings.top_k,
            "modes": list(search_settings.modes),
            "thread_id": thread_id,
        },
    }


async def finalize_diary(
    *,
    messages: list[dict[str, Any]],
    thread_id: str,
    search_settings: SearchSettings,
) -> tuple[str, int, DiaryAnalysis]:
    analysis = await analyze_diary(messages)
    document = build_diary_document(
        messages=messages,
        analysis=analysis,
        thread_id=thread_id,
        search_settings=search_settings,
    )
    try:
        result = await _MINIRAG_CLIENT.bulk_insert([document])
    except MiniRagError as exc:
        raise DiaryAnalysisError(f"MiniRAG bulk insert failed: {exc}") from exc
    inserted = int(result.get("inserted", 1))
    return document["doc_id"], inserted, analysis


def _extract_search_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    # 旧形式: items/documents など
    candidates = payload.get("items") or payload.get("documents") or []
    if isinstance(candidates, list) and candidates:
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            items.append(
                {
                    "doc_id": entry.get("doc_id") or entry.get("id") or "",
                    "summary": entry.get("summary") or "",
                    "body": entry.get("body") or "",
                }
            )
        return items

    # MiniRAG 形式: results -> sources / answer.provenance.chunks
    results = payload.get("results") or []
    if not isinstance(results, list):
        return items

    for result in results:
        if not isinstance(result, dict):
            continue
        answer = result.get("answer")
        provenance = answer.get("provenance") if isinstance(answer, dict) else None
        chunks = provenance.get("chunks") if isinstance(provenance, dict) else None

        if isinstance(chunks, list) and chunks:
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                content = str(chunk.get("content") or "").strip()
                if not content:
                    continue
                items.append(
                    {
                        "doc_id": chunk.get("full_doc_id")
                        or chunk.get("doc_id")
                        or chunk.get("chunk_id")
                        or "",
                        "summary": content,
                        "body": content,
                    }
                )
            continue

        sources = result.get("sources") or []
        if not isinstance(sources, list):
            continue
        for source in sources:
            if isinstance(source, dict):
                content = str(
                    source.get("content")
                    or source.get("body")
                    or source.get("summary")
                    or ""
                ).strip()
                doc_id = source.get("doc_id") or source.get("id") or ""
            else:
                content = str(source).strip()
                doc_id = ""
            if not content:
                continue
            items.append(
                {
                    "doc_id": doc_id,
                    "summary": content,
                    "body": content,
                }
            )

    return items


async def search_diary(
    *,
    query: str,
    thread_id: str,
    top_k: int | None = None,
) -> dict[str, Any]:
    settings = get_search_settings(thread_id)
    if not settings.enabled:
        return {"items": [], "disabled": True}
    query = query.strip()
    if not query:
        raise DiaryValidationError("Search query is empty.")
    effective_top_k = top_k if top_k is not None else settings.top_k
    try:
        modes = list(settings.modes) if settings.modes else None
        payload = await _MINIRAG_CLIENT.search(query, effective_top_k, modes)
    except MiniRagError as exc:
        logger.warning("MiniRAG search failed: %s", exc)
        return {"items": [], "error": "MiniRAG unavailable"}
    return {"items": _extract_search_items(payload)}
