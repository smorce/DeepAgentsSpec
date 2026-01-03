from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from src import config


PROFILE_DIR = config.ROOT_DIR / "profiling"
PROFILE_PATH = PROFILE_DIR / "user_profile.yaml"
PROFILE_DEFAULT_PATH = PROFILE_DIR / "user_profile.default.yaml"


class ProfileStoreError(RuntimeError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProfileStoreError(f"Profile file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except Exception as exc:  # pragma: no cover - defensive
        raise ProfileStoreError(f"Failed to load profile YAML: {path}") from exc
    if not isinstance(data, dict):
        raise ProfileStoreError(f"Profile YAML must be a mapping: {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
    except Exception as exc:  # pragma: no cover - defensive
        raise ProfileStoreError(f"Failed to write profile YAML: {path}") from exc


def load_default_profile() -> dict[str, Any]:
    return _load_yaml(PROFILE_DEFAULT_PATH)


def load_profile() -> dict[str, Any]:
    if PROFILE_PATH.exists():
        return _load_yaml(PROFILE_PATH)
    default_profile = load_default_profile()
    _write_yaml(PROFILE_PATH, default_profile)
    return copy.deepcopy(default_profile)


def save_profile(profile: dict[str, Any]) -> None:
    _write_yaml(PROFILE_PATH, profile)


def normalize_path(path: list[str]) -> list[str]:
    return [segment.strip() for segment in path if isinstance(segment, str) and segment.strip()]


def path_exists(schema: dict[str, Any], path: list[str]) -> bool:
    current: Any = schema
    for segment in path:
        if not isinstance(current, dict):
            return False
        if segment not in current:
            return False
        current = current[segment]
    return True


def ensure_path(profile: dict[str, Any], schema: dict[str, Any], path: list[str]) -> bool:
    current_profile: Any = profile
    current_schema: Any = schema
    for segment in path[:-1]:
        if not isinstance(current_schema, dict) or segment not in current_schema:
            return False
        current_schema = current_schema[segment]
        if not isinstance(current_profile, dict):
            return False
        if segment not in current_profile or not isinstance(current_profile.get(segment), dict):
            current_profile[segment] = copy.deepcopy(current_schema)
        current_profile = current_profile[segment]
    return True


def apply_value(profile: dict[str, Any], path: list[str], value: str) -> bool:
    if not path:
        return False
    current: Any = profile
    for segment in path[:-1]:
        if not isinstance(current, dict) or segment not in current:
            return False
        current = current[segment]
    if not isinstance(current, dict) or path[-1] not in current:
        return False
    current[path[-1]] = value
    return True
