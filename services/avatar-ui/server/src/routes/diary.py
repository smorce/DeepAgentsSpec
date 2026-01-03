from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src import config
from src.diary_service import (
    DiaryAnalysisError,
    DiaryValidationError,
    SearchSettings,
    finalize_diary,
    search_diary as run_search_diary,
    set_search_settings,
)


router = APIRouter()


class DiaryMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime | None = None


class SearchSettingsModel(BaseModel):
    enabled: bool
    top_k: int = Field(ge=1, le=10)


class DiaryAnalysisModel(BaseModel):
    title: str
    importance_score: int = Field(ge=1, le=10)
    summary: str
    semantic_memory: str
    episodic_memory: str


class FinalizeDiaryRequest(BaseModel):
    workspace: str
    thread_id: str
    messages: list[DiaryMessage]
    search_settings: SearchSettingsModel


class FinalizeDiaryResponse(BaseModel):
    doc_id: str
    inserted: int
    analysis: DiaryAnalysisModel


class SearchSettingsRequest(BaseModel):
    thread_id: str
    settings: SearchSettingsModel


class SearchSettingsResponse(BaseModel):
    applied: bool


class ErrorResponse(BaseModel):
    message: str


@router.post(
    "/agui/diary/finalize",
    response_model=FinalizeDiaryResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def finalize_diary_route(request: FinalizeDiaryRequest) -> FinalizeDiaryResponse:
    if request.workspace != config.MINIRAG_WORKSPACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace.",
        )
    settings = SearchSettings(
        enabled=request.search_settings.enabled,
        top_k=request.search_settings.top_k,
    )
    set_search_settings(request.thread_id, settings)
    try:
        doc_id, inserted, analysis = await finalize_diary(
            messages=[message.model_dump() for message in request.messages],
            thread_id=request.thread_id,
            search_settings=settings,
        )
    except DiaryValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DiaryAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return FinalizeDiaryResponse(
        doc_id=doc_id,
        inserted=inserted,
        analysis=DiaryAnalysisModel(
            title=analysis.title,
            importance_score=analysis.importance_score,
            summary=analysis.summary,
            semantic_memory=analysis.semantic_memory,
            episodic_memory=analysis.episodic_memory,
        ),
    )


@router.post(
    "/agui/diary/search-settings",
    response_model=SearchSettingsResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_search_settings(request: SearchSettingsRequest) -> SearchSettingsResponse:
    settings = SearchSettings(
        enabled=request.settings.enabled,
        top_k=request.settings.top_k,
    )
    set_search_settings(request.thread_id, settings)
    return SearchSettingsResponse(applied=True)


async def search_diary(
    query: str,
    thread_id: str | None = None,
    top_k: int | None = None,
) -> dict:
    """Search past diary entries and return doc_id/summary/body items."""
    thread = thread_id or config.THREAD_ID
    try:
        return await run_search_diary(query=query, thread_id=thread, top_k=top_k)
    except DiaryValidationError as exc:
        return {"items": [], "error": str(exc)}
