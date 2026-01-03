from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from google import genai

from src import config
from src.profile_store import (
    apply_value,
    ensure_path,
    load_default_profile,
    load_profile,
    normalize_path,
    path_exists,
    save_profile,
)


logger = logging.getLogger(__name__)


class ProfilingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProfileUpdate:
    path: list[str]
    value: str
    confidence: float
    evidence: str | None = None


@dataclass(frozen=True)
class ProfilingStatus:
    status: str
    message: str | None = None


def build_profile_prompt(transcript: str, schema: dict[str, Any]) -> str:
    schema_overview = json.dumps(schema, ensure_ascii=False)
    return (
        "あなたはユーザーのプロフィール更新を支援するアシスタントです。"
        "以下の会話からユーザーの価値観・思考傾向・言葉遣いなどを推定し、"
        "差分更新だけを JSON で返してください。"
        "必ず JSON のみを返し、フォーマットは次の通りです:\n"
        "{\"updates\": ["
        "{\"path\": [\"セクション\", \"項目\"], "
        "\"value\": \"更新値\", \"confidence\": 0.0, "
        "\"evidence\": \"短い根拠\"}]}\n"
        "path は次のスキーマ内のキーに限定してください。\n"
        f"profile_schema: {schema_overview}\n\n"
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
        raise ProfilingError("Gemini response did not include JSON payload.")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ProfilingError(f"Failed to parse JSON payload: {exc}") from exc


def parse_profile_updates(payload: dict[str, Any]) -> list[ProfileUpdate]:
    raw_updates = payload.get("updates")
    if not isinstance(raw_updates, list):
        raise ProfilingError("updates is missing or invalid.")
    updates: list[ProfileUpdate] = []
    for entry in raw_updates:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not isinstance(path, list):
            continue
        value = str(entry.get("value") or "").strip()
        try:
            confidence = float(entry.get("confidence"))
        except (TypeError, ValueError):
            continue
        evidence = entry.get("evidence")
        normalized_path = normalize_path(path)
        if not normalized_path:
            continue
        updates.append(
            ProfileUpdate(
                path=normalized_path,
                value=value,
                confidence=confidence,
                evidence=str(evidence).strip() if isinstance(evidence, str) and evidence else None,
            )
        )
    return updates


def apply_profile_updates(
    profile: dict[str, Any],
    schema: dict[str, Any],
    updates: list[ProfileUpdate],
    min_confidence: float,
) -> tuple[dict[str, Any], int]:
    applied = 0
    for update in updates:
        if update.confidence < min_confidence:
            continue
        if not update.value:
            continue
        if not path_exists(schema, update.path):
            continue
        if not ensure_path(profile, schema, update.path):
            continue
        if not apply_value(profile, update.path, update.value):
            continue
        applied += 1
    return profile, applied


def update_profile_from_transcript(transcript: str) -> ProfilingStatus:
    transcript = transcript.strip()
    if not transcript:
        return ProfilingStatus(status="ok")

    schema = load_default_profile()
    profile = load_profile()
    prompt = build_profile_prompt(transcript, schema)

    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=config.PROFILING_MODEL,
        contents=prompt,
    )
    text = _extract_response_text(response)
    if not text:
        raise ProfilingError("Gemini response was empty.")
    payload = _extract_json_payload(text)
    updates = parse_profile_updates(payload)
    updated_profile, applied = apply_profile_updates(
        profile,
        schema,
        updates,
        config.PROFILING_MIN_CONFIDENCE,
    )
    if applied > 0:
        save_profile(updated_profile)
    return ProfilingStatus(status="ok")


def run_profiling(transcript: str) -> ProfilingStatus:
    try:
        return update_profile_from_transcript(transcript)
    except ProfilingError as exc:
        logger.warning("Profiling update failed: %s", exc)
        return ProfilingStatus(status="failed", message=str(exc))
    except Exception as exc:
        logger.warning("Profiling update crashed: %s", exc)
        return ProfilingStatus(status="failed", message="Profiling error")
