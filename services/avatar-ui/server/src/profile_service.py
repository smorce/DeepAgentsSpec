from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from src import config
from src.litellm_client import completion_with_purpose
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
    applied: int = 0


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


def _build_completion_kwargs() -> dict[str, Any]:
    if config.LLM_PROVIDER.lower() != "openrouter":
        return {}
    if not config.REASONING_ENABLED:
        return {}
    return {
        "reasoning": {"enabled": True},
        "include_reasoning": True,
    }


def _extract_response_text(response: Any) -> str:
    if response is None:
        return ""
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
    return ""


def _extract_json_payload(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ProfilingError("LLM response did not include JSON payload.")
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
        return ProfilingStatus(status="ok", applied=0)

    schema = load_default_profile()
    profile = load_profile()
    prompt = build_profile_prompt(transcript, schema)

    response = completion_with_purpose(
        purpose="プロフィール推定",
        model=config.PROFILING_LITELLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        **_build_completion_kwargs(),
    )
    text = _extract_response_text(response)
    if not text:
        raise ProfilingError("LLM response was empty.")
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
    return ProfilingStatus(status="ok", applied=applied)


def run_profiling(transcript: str) -> ProfilingStatus:
    try:
        return update_profile_from_transcript(transcript)
    except ProfilingError as exc:
        logger.warning("Profiling update failed: %s", exc)
        return ProfilingStatus(status="failed", message=str(exc), applied=0)
    except Exception as exc:
        logger.warning("Profiling update crashed: %s", exc)
        message = str(exc).strip()
        return ProfilingStatus(
            status="failed",
            message=message or "Profiling error",
            applied=0,
        )
