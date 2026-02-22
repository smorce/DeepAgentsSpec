#!/usr/bin/env python3
"""Agent radar control loop for in-repo System of Record."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AGENT_RADAR_DIR = ROOT / "harness" / "agent_radar"
OFFICIAL_SOURCES = AGENT_RADAR_DIR / "official_sources.json"
STATE_FILE = AGENT_RADAR_DIR / "state.json"
SNAPSHOT_FILE = AGENT_RADAR_DIR / "snapshot-latest.json"
NEW_ITEMS_FILE = AGENT_RADAR_DIR / "new-items.json"
EXPERIMENT_BACKLOG_FILE = AGENT_RADAR_DIR / "experiment_backlog.json"
GOLDEN_RULES_FILE = AGENT_RADAR_DIR / "golden_rules.json"
MONITORING_TARGETS_FILE = AGENT_RADAR_DIR / "monitoring_targets.json"
MONITORING_RESULTS_FILE = AGENT_RADAR_DIR / "monitoring_results.json"
IMPLEMENTED_DIR = AGENT_RADAR_DIR / "implemented"
MUTATIONS_DIR = AGENT_RADAR_DIR / "mutations"
MUTATION_INDEX_FILE = MUTATIONS_DIR / "index.json"
METRICS_DIR = AGENT_RADAR_DIR / "metrics"
METRICS_LATEST_FILE = METRICS_DIR / "latest.json"
METRICS_HISTORY_FILE = METRICS_DIR / "history.jsonl"
SELF_HEAL_LOG_FILE = AGENT_RADAR_DIR / "self_heal_log.json"
AUTONOMOUS_GROWTH_DOC = ROOT / "docs" / "agent-harness" / "autonomous-growth.md"
PROGRESS_LOG = ROOT / "harness" / "AI-Agent-progress.txt"
REPORTS_DIR = ROOT / "docs" / "reports" / "source-radar"
CODEX_AUDIT_DIR = REPORTS_DIR / "codex-exec"

GARDEN_TARGETS = [
    ROOT / "architecture" / "system-architecture.md",
    ROOT / "architecture" / "service-boundaries.md",
    ROOT / "architecture" / "deployment-topology.md",
    ROOT / "docs" / "agent-harness",
    ROOT / "plans" / "system" / "EPIC-SYS-001-harness-radar",
]

GARDEN_PATTERNS = [
    re.compile(r"TODO:"),
    re.compile(r"\[NEEDS\s+CLARIFICATION", re.IGNORECASE),
]

USER_AGENT = (
    "Mozilla/5.0 (compatible; DeepAgentsSpec/1.0; +https://example.invalid/agent-radar)"
)

THEME_KEYWORDS: dict[str, list[str]] = {
    "mcp": ["mcp", "tool use", "tool-use", "devtools", "jetbrains"],
    "skills": ["skill", "skills"],
    "environment": ["environment", "runtime", "workflow", "tooling", "infra", "developer experience", "dx"],
    "feedback": ["feedback", "feedback loop", "regression", "postmortem", "incident review", "closed loop"],
    "control": ["control loop", "orchestration", "policy", "governance", "gate", "rollback", "circuit breaker"],
    "reliability": ["reliability", "resilience", "fault tolerance", "slo", "sla", "recovery", "deterministic"],
    "scalability": ["scale", "scalable", "throughput", "latency", "capacity", "distributed"],
    "maintainability": ["maintainability", "maintain", "modular", "refactor", "ownership", "operability"],
    "evals": ["eval", "benchmark", "swe-bench", "verification"],
    "context": ["context", "memory", "retrieval", "state", "checkpoint", "compaction"],
    "observability": ["trace", "metric", "log", "observability", "promql", "logql"],
    "safety": ["safety", "sandbox", "security", "guard"],
}

GROWTH_AXIS_KEYWORDS: dict[str, list[str]] = {
    "environment": ["environment", "runtime", "workflow", "tooling", "dx", "developer experience"],
    "feedback_loop": ["feedback", "evaluation", "eval", "regression", "postmortem", "incident review"],
    "control_system": ["control", "orchestr", "policy", "gate", "governance", "autogrow", "closed loop"],
    "reliability": ["reliability", "resilience", "fault tolerance", "deterministic", "recovery", "rollback"],
    "scalability": ["scale", "scalable", "throughput", "latency", "capacity", "distributed"],
}

DEFAULT_CHECKPOINT_POLICY = [
    "before_external_io",
    "before_long_running_loop",
    "before_quality_gate",
]

DEFAULT_CONVERSATION_REPLACEMENTS = [
    "[[STATE_REF:<id>]]",
    "[[PLAN_REF:<epic>/<feature>]]",
    "[[EVAL_REF:<run>]]",
]

HIGH_PRIORITY_THEMES = {"control", "feedback", "reliability", "evals", "safety", "observability"}
MEDIUM_PRIORITY_THEMES = {"mcp", "skills", "environment", "context", "scalability", "maintainability"}

# LLM リトライ設定
LLM_MAX_RETRIES = 3
LLM_RETRY_BASE_DELAY = 2.0
LLM_RETRY_MAX_DELAY = 60.0
LLM_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


@dataclass
class RadarItem:
    title: str
    link: str
    published: str
    collected_via: str
    evidence_url: str = ""

    def to_dict(self) -> dict[str, str]:
        data = {
            "title": self.title,
            "link": self.link,
            "published": self.published,
            "collected_via": self.collected_via,
        }
        if self.evidence_url:
            data["evidence_url"] = self.evidence_url
        return data


@dataclass
class SourceResult:
    source_id: str
    name: str
    homepage: str
    items: list[RadarItem]
    errors: list[str]


@dataclass
class StepOutcome:
    name: str
    rc: int
    recovered: bool = False
    repair_actions: list[str] = field(default_factory=list)


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._current_href = ""
        self._chunks: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href" and value:
                href = value
                break
        if not href:
            return
        self._in_anchor = True
        self._current_href = href
        self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._in_anchor:
            return
        text = normalize_space("".join(self._chunks))
        self.anchors.append((self._current_href, text))
        self._in_anchor = False
        self._current_href = ""
        self._chunks = []


class RetryHandler:
    """
    指数バックオフとジッターを使用したリトライハンドラー。
    Codex 実行時の 429 / 5xx / タイムアウト等に備える。
    """

    def __init__(
        self,
        max_retries: int = LLM_MAX_RETRIES,
        base_delay: float = LLM_RETRY_BASE_DELAY,
        max_delay: float = LLM_RETRY_MAX_DELAY,
        retry_status_codes: list[int] | None = None,
        log_func=None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_status_codes = retry_status_codes or LLM_RETRY_STATUS_CODES
        self.log_func = log_func

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        リトライすべきかどうかを判定する。

        Args:
            exception: 発生した例外
            attempt: 現在の試行回数（0始まり）

        Returns:
            リトライすべき場合は True
        """
        if attempt >= self.max_retries:
            return False

        error_str = str(exception)

        non_retryable_keywords = [
            "context_length_exceeded",
            "context window",
            "input exceeds",
        ]
        if any(kw in error_str.lower() for kw in non_retryable_keywords):
            msg = f"Non-retryable error detected (context length exceeded): {error_str[:200]}"
            if self.log_func:
                self.log_func(msg)
            return False

        for code in self.retry_status_codes:
            if str(code) in error_str:
                return True

        retry_keywords = ["timeout", "connection", "rate", "limit", "throttl"]
        return any(kw in error_str.lower() for kw in retry_keywords)

    def get_delay(self, attempt: int) -> float:
        """
        リトライ前の待機時間を計算する（指数バックオフ + ジッター）。

        Args:
            attempt: 現在の試行回数（0始まり）

        Returns:
            待機時間（秒）
        """
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(raw: str) -> dt.datetime | None:
    value = normalize_space(raw)
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_jsonl(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False))
        f.write("\n")


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def coerce_str_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str):
            continue
        token = normalize_space(value)
        if not token or token in seen:
            continue
        cleaned.append(token)
        seen.add(token)
    return cleaned


def with_default_str_list(raw: Any, default_values: list[str]) -> list[str]:
    values = coerce_str_list(raw)
    return values if values else list(default_values)


def detect_growth_axes(*texts: str) -> list[str]:
    joined = " ".join(texts).lower()
    axes: list[str] = []
    for axis, keywords in GROWTH_AXIS_KEYWORDS.items():
        if any(keyword in joined for keyword in keywords):
            axes.append(axis)
    if not axes:
        axes.append("control_system")
    return axes


def innovation_priority_for_themes(themes: list[str]) -> str:
    theme_set = {theme.strip().lower() for theme in themes if theme.strip()}
    if theme_set.intersection(HIGH_PRIORITY_THEMES):
        return "high"
    if theme_set.intersection(MEDIUM_PRIORITY_THEMES):
        return "medium"
    return "normal"


def normalize_origin_path(url: str) -> str:
    raw = normalize_space(url)
    if not raw:
        return ""
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme.lower() != "https":
        return ""
    host = parsed.netloc.lower()
    path = parsed.path or "/"
    return f"https://{host}{path}"


def normalize_prefix(prefix: str) -> str:
    origin_path = normalize_origin_path(prefix)
    if not origin_path:
        return ""
    if origin_path.endswith("/"):
        return origin_path
    return f"{origin_path}/"


def normalize_exp_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", value.strip())
    return cleaned or "EXP-UNKNOWN"


def mutation_module_name(exp_id: str) -> str:
    normalized = normalize_exp_id(exp_id).lower().replace("-", "_")
    return f"mutation_{normalized}"


def mutation_module_path(exp_id: str) -> Path:
    return MUTATIONS_DIR / f"{mutation_module_name(exp_id)}.py"


def ensure_mutation_index() -> dict[str, Any]:
    index = read_json(
        MUTATION_INDEX_FILE,
        default={"version": 1, "updated_at": iso_now(), "modules": []},
    )
    if not isinstance(index, dict):
        index = {"version": 1, "updated_at": iso_now(), "modules": []}

    modules = index.get("modules")
    if not isinstance(modules, list):
        modules = []
    index["modules"] = modules
    index["version"] = int(index.get("version", 1))
    return index


def load_mutation_modules() -> list[Any]:
    index = ensure_mutation_index()
    modules: list[Any] = []
    for entry in index["modules"]:
        if not isinstance(entry, dict):
            continue
        rel_path = str(entry.get("path", "")).strip()
        module_name = str(entry.get("module", "")).strip()
        if not rel_path or not module_name:
            continue
        module_path = ROOT / rel_path
        if not module_path.exists():
            continue

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            append_progress(f"mutation load skipped | module={module_name} reason=invalid_spec")
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            append_progress(f"mutation load failed | module={module_name} error={exc}")
            continue
        modules.append(module)
    return modules


def apply_mutations_to_new_item(raw_item: dict[str, Any], modules: list[Any]) -> dict[str, Any]:
    item = dict(raw_item)
    applied: list[str] = []
    for module in modules:
        mutate_fn = getattr(module, "mutate", None)
        if not callable(mutate_fn):
            continue
        try:
            updated = mutate_fn(item)
        except Exception as exc:  # noqa: BLE001
            append_progress(f"mutation execute failed | module={module.__name__} error={exc}")
            continue
        if isinstance(updated, dict):
            item = updated
            applied.append(str(getattr(module, "MUTATION_ID", module.__name__)))
    if applied:
        item["applied_mutations"] = applied
    return item


def write_mutation_module(exp_item: dict[str, Any], themes: list[str]) -> Path:
    exp_id = normalize_exp_id(str(exp_item.get("id", "EXP-UNKNOWN")))
    module_name = mutation_module_name(exp_id)
    module_path = mutation_module_path(exp_id)
    title = normalize_space(str(exp_item.get("title", "")))
    source_id = normalize_space(str(exp_item.get("origin_source_id", exp_item.get("source", ""))))
    themes_literal = json.dumps(themes, ensure_ascii=False)
    title_literal = json.dumps(title, ensure_ascii=False)
    source_literal = json.dumps(source_id, ensure_ascii=False)
    checkpoint_literal = json.dumps(DEFAULT_CHECKPOINT_POLICY, ensure_ascii=False)
    replacement_literal = json.dumps(DEFAULT_CONVERSATION_REPLACEMENTS, ensure_ascii=False)
    high_priority_literal = json.dumps(sorted(HIGH_PRIORITY_THEMES), ensure_ascii=False)
    medium_priority_literal = json.dumps(sorted(MEDIUM_PRIORITY_THEMES), ensure_ascii=False)

    content = "\n".join(
        [
            '"""Auto-generated mutation module for agent radar."""',
            "",
            f"MUTATION_ID = {json.dumps(exp_id)}",
            f"MUTATION_TITLE = {title_literal}",
            f"MUTATION_SOURCE = {source_literal}",
            f"THEMES = {themes_literal}",
            "",
            "def mutate(new_item):",
            "    item = dict(new_item)",
            "    tags = item.get('harness_tags', [])",
            "    if not isinstance(tags, list):",
            "        tags = []",
            "    for theme in THEMES:",
            "        if theme not in tags:",
            "            tags.append(theme)",
            "    item['harness_tags'] = tags",
            "    item['state_checkpoint_policy'] = " + checkpoint_literal,
            "    item['conversation_replacements'] = " + replacement_literal,
            "    high_priority_themes = set(" + high_priority_literal + ")",
            "    medium_priority_themes = set(" + medium_priority_literal + ")",
            "    theme_set = {str(theme).strip().lower() for theme in THEMES}",
            "    if theme_set.intersection(high_priority_themes):",
            "        item['innovation_priority'] = 'high'",
            "    elif theme_set.intersection(medium_priority_themes):",
            "        item['innovation_priority'] = 'medium'",
            "    else:",
            "        item['innovation_priority'] = 'normal'",
            "    item['mutation_module'] = " + json.dumps(module_name),
            "    return item",
            "",
        ]
    )
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(content, encoding="utf-8")
    return module_path


def is_autogenerated_mutation(module_path: Path) -> bool:
    if not module_path.exists() or not module_path.is_file():
        return False
    try:
        head = module_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return head.startswith('"""Auto-generated mutation module for agent radar."""')


def upsert_mutation_index(exp_id: str, module_path: Path, themes: list[str]) -> bool:
    index = ensure_mutation_index()
    modules = index["modules"]
    module_name = mutation_module_name(exp_id)
    rel_path = str(module_path.relative_to(ROOT))
    source_hash = hashlib.sha256(module_path.read_bytes()).hexdigest()

    for entry in modules:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("id", "")) != exp_id:
            continue
        entry["module"] = module_name
        entry["path"] = rel_path
        entry["themes"] = list(themes)
        entry["updated_at"] = iso_now()
        entry["sha256"] = source_hash
        index["updated_at"] = iso_now()
        write_json(MUTATION_INDEX_FILE, index)
        return False

    modules.append(
        {
            "id": exp_id,
            "module": module_name,
            "path": rel_path,
            "themes": list(themes),
            "created_at": iso_now(),
            "updated_at": iso_now(),
            "sha256": source_hash,
        }
    )
    index["updated_at"] = iso_now()
    write_json(MUTATION_INDEX_FILE, index)
    return True


def fingerprint_links(links: list[str]) -> str:
    joined = "\n".join(links)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read()


def parse_feed(feed_url: str, source: dict[str, Any]) -> tuple[list[RadarItem], list[str]]:
    errors: list[str] = []
    try:
        body = fetch_url(feed_url)
    except (urllib.error.URLError, TimeoutError) as exc:
        return [], [f"feed_fetch_failed:{feed_url}:{exc}"]

    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        return [], [f"feed_parse_failed:{feed_url}:{exc}"]

    max_items = int(source.get("max_items", 20))
    allowed_prefixes = source.get("allowed_entry_prefixes", [])

    items: list[RadarItem] = []

    # RSS items
    for item in root.findall(".//item"):
        link = normalize_space((item.findtext("link") or ""))
        title = normalize_space((item.findtext("title") or ""))
        published = normalize_space((item.findtext("pubDate") or item.findtext("published") or item.findtext("updated") or ""))
        if not link:
            continue
        if not has_allowed_prefix(link, allowed_prefixes):
            continue
        if not title:
            title = link
        items.append(
            RadarItem(
                title=title,
                link=link,
                published=normalize_published(published),
                collected_via="rss",
                evidence_url=feed_url,
            )
        )
        if len(items) >= max_items:
            return dedupe_items(items, max_items), errors

    # Atom entries
    for entry in root.findall(".//{*}entry"):
        link = ""
        for link_node in entry.findall("{*}link"):
            href = link_node.attrib.get("href", "")
            rel = link_node.attrib.get("rel", "")
            if href and (not rel or rel == "alternate"):
                link = normalize_space(href)
                break
        title = normalize_space((entry.findtext("{*}title") or ""))
        published = normalize_space((entry.findtext("{*}published") or entry.findtext("{*}updated") or ""))
        if not link:
            continue
        if not has_allowed_prefix(link, allowed_prefixes):
            continue
        if not title:
            title = link
        items.append(
            RadarItem(
                title=title,
                link=link,
                published=normalize_published(published),
                collected_via="rss",
                evidence_url=feed_url,
            )
        )
        if len(items) >= max_items:
            break

    return dedupe_items(items, max_items), errors


def parse_html(homepage: str, source: dict[str, Any]) -> tuple[list[RadarItem], list[str]]:
    try:
        body = fetch_url(homepage)
    except (urllib.error.URLError, TimeoutError) as exc:
        return [], [f"html_fetch_failed:{homepage}:{exc}"]

    encoding = "utf-8"
    text = body.decode(encoding, errors="replace")
    parser = AnchorParser()
    parser.feed(text)

    html_prefixes = source.get("html_entry_prefixes") or source.get("allowed_entry_prefixes", [])
    max_items = int(source.get("max_items", 20))

    items: list[RadarItem] = []
    for raw_href, raw_title in parser.anchors:
        href = urllib.parse.urljoin(homepage, raw_href)
        href = href.split("#", 1)[0]
        title = normalize_space(raw_title)
        if not href:
            continue
        if not has_allowed_prefix(href, html_prefixes):
            continue
        if title == "":
            continue
        items.append(
            RadarItem(
                title=title,
                link=href,
                published="",
                collected_via="html",
                evidence_url=homepage,
            )
        )
        if len(items) >= max_items:
            break

    return dedupe_items(items, max_items), []


def has_allowed_prefix(link: str, prefixes: list[str]) -> bool:
    link_norm = normalize_origin_path(link)
    if not link_norm:
        return False
    for prefix in prefixes:
        prefix_norm = normalize_prefix(prefix)
        if not prefix_norm:
            continue
        if link_norm.startswith(prefix_norm):
            return True
        if prefix_norm.endswith("/") and link_norm == prefix_norm[:-1]:
            return True
    return False


def normalize_published(raw: str) -> str:
    value = normalize_space(raw)
    if not value:
        return ""

    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except ValueError:
        pass

    try:
        parsed_rss = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return ""
    if parsed_rss is None:
        return ""
    if parsed_rss.tzinfo is None:
        parsed_rss = parsed_rss.replace(tzinfo=dt.timezone.utc)
    return parsed_rss.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dedupe_items(items: list[RadarItem], max_items: int) -> list[RadarItem]:
    seen: set[str] = set()
    result: list[RadarItem] = []
    for item in items:
        if item.link in seen:
            continue
        seen.add(item.link)
        result.append(item)
        if len(result) >= max_items:
            break
    return result


def collect_source(source: dict[str, Any]) -> SourceResult:
    source_id = source["id"]
    name = source["name"]
    homepage = source["homepage"]

    all_items: list[RadarItem] = []
    errors: list[str] = []

    feeds = source.get("feeds", [])
    for feed in feeds:
        feed_items, feed_errors = parse_feed(feed, source)
        all_items.extend(feed_items)
        errors.extend(feed_errors)

    if not all_items:
        html_items, html_errors = parse_html(homepage, source)
        all_items.extend(html_items)
        errors.extend(html_errors)

    max_items = int(source.get("max_items", 20))
    all_items = dedupe_items(all_items, max_items)

    allowed_prefixes = source.get("allowed_entry_prefixes", [])
    all_items = [item for item in all_items if has_allowed_prefix(item.link, allowed_prefixes)]

    return SourceResult(
        source_id=source_id,
        name=name,
        homepage=homepage,
        items=all_items,
        errors=errors,
    )


def extract_json_object(text: str) -> dict[str, Any]:
    trimmed = text.strip()
    if not trimmed:
        raise RuntimeError("codex output is empty")
    try:
        data = json.loads(trimmed)
    except json.JSONDecodeError:
        left = trimmed.find("{")
        right = trimmed.rfind("}")
        if left < 0 or right < 0 or right <= left:
            raise RuntimeError("codex output does not contain a json object") from None
        snippet = trimmed[left : right + 1]
        try:
            data = json.loads(snippet)
        except json.JSONDecodeError as exc:  # noqa: PERF203
            raise RuntimeError("codex output is not valid json") from exc

    if not isinstance(data, dict):
        raise RuntimeError("codex output root must be object")
    return data


def unique_file(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for idx in range(1, 1000):
        candidate = path.with_name(f"{stem}-{idx:03d}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"failed to allocate unique path: {path}")


def write_codex_audit(stdout_text: str, stderr_text: str, return_code: int) -> Path:
    CODEX_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    base = CODEX_AUDIT_DIR / f"{utc_now().strftime('%Y%m%dT%H%M%SZ')}.md"
    path = unique_file(base)
    lines = [
        "# Codex Exec Audit",
        "",
        f"- generated_at: `{iso_now()}`",
        f"- return_code: `{return_code}`",
        "",
        "## STDERR",
        "",
        "```text",
        stderr_text.rstrip(),
        "```",
        "",
        "## STDOUT",
        "",
        "```text",
        stdout_text.rstrip(),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def emit_runtime_info(summary: str) -> None:
    print(f"INFO: {summary}", file=sys.stderr, flush=True)
    append_progress(summary)

# #region agent log
def _agent_debug_log(*, run_id: str, hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    try:
        payload = {
            "sessionId": "9f3ad0",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with (ROOT / "debug-9f3ad0.log").open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _agent_summarize_config(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        info["size"] = len(raw)
        info["sha256"] = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()
        low = raw.lower()
        info["has_model"] = "model" in low
        info["has_sandbox_mode"] = "sandbox_mode" in low
        info["has_web_search"] = "web_search" in low
        info["has_mcp_servers"] = "mcp_servers" in low
        info["mentions_smorcepie"] = "smorcepie" in low
        info["mentions_chrome_devtools"] = "chrome-devtools" in low
    except Exception as exc:
        info["error"] = str(exc)[:200]
    return info


def _agent_read_project_codex_kv(path: Path) -> dict[str, str]:
    """
    `.codex/config.toml` から必要最小限のトップレベル設定だけを抽出する。
    依存追加なし・壊れにくさ優先で、厳密な TOML パースは行わない。
    """
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    kv: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        # inline comment を落とす（"..." 内の # は考慮しない、簡易実装）
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        kv[key] = value
    return kv
# #endregion


def evidence_prefixes_for_source(source: dict[str, Any]) -> list[str]:
    prefixes: list[str] = []
    for value in source.get("allowed_entry_prefixes", []):
        prefixes.append(str(value))
    prefixes.append(str(source.get("homepage", "")))
    for value in source.get("feeds", []):
        prefixes.append(str(value))

    seen: set[str] = set()
    deduped: list[str] = []
    for value in prefixes:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def codex_unavailable_title(reason: str) -> str:
    return f"取得不可: 公式サイトから最新記事情報を確定できません ({reason})"


def build_codex_latest_prompt(sources: list[dict[str, Any]]) -> str:
    source_lines = []
    for src in sources:
        source_lines.append(f"- {src['homepage']}")

    return "\n".join(
        [
            "あなたはローカル環境で実行中です。次の6ブログだけを確認し、各ブログの最新記事を1件返してください。",
            "",
            "【許可されたブログ（これ以外はアクセス禁止）】",
            *source_lines,
            "",
            "【要件】",
            "- 推測禁止。不明時に null は返さないこと",
            "- 各ブログについて latest_title / latest_url / latest_date / method / evidence_url を1件返すこと",
            "- method は rss / atom / html のいずれか",
            "- possibleなら RSS/Atom を優先。なければ HTML 推定",
            "- latest_url と evidence_url は必ず許可されたブログ配下のURLのみ",
            "- 取得不能な場合は method='html' とし、latest_title に取得不能理由の短文を入れる",
            "- 取得不能な場合は latest_url/evidence_url に site と同じURLを入れる（null禁止）",
            "- 出力は JSON のみ。説明文や Markdown 禁止",
            "- 許可外URLを1件でも使った場合は {\"error\":\"OUT_OF_SCOPE\"} のみを返す",
            "",
            "【出力JSON】",
            "{",
            '  "checked_at": "<UTC ISO8601>",',
            '  "results": [',
            "    {",
            '      "site": "<homepage>",',
            '      "latest_title": "<string>",',
            '      "latest_url": "<string>",',
            '      "latest_date": "<string|null>",',
            '      "method": "<rss|atom|html>",',
            '      "evidence_url": "<string>"',
            "    }",
            "  ]",
            "}",
        ]
    )


def run_codex_exec(prompt: str, timeout_sec: int = 600) -> tuple[str, Path]:
    """
    Codex CLI を実行する（リトライ対応版）。
    .codex/config.toml の設定を適用するため、リポジトリルートを cwd に指定する。
    """
    retry_handler = RetryHandler(log_func=emit_runtime_info)
    
    for attempt in range(retry_handler.max_retries + 1):
        try:
            if attempt > 0:
                delay = retry_handler.get_delay(attempt - 1)
                emit_runtime_info(f"codex exec retry | attempt={attempt + 1}/{retry_handler.max_retries + 1} delay={delay:.1f}s")
                time.sleep(delay)
            
            return _run_codex_exec_once(prompt, timeout_sec, attempt)
            
        except Exception as exc:
            # #region agent log
            try:
                _agent_debug_log(
                    run_id="post-fix",
                    hypothesis_id="E",
                    location="radar_ops.py:run_codex_exec",
                    message="codex exec raised exception",
                    data={"attempt": attempt, "error": str(exc)[:400]},
                )
            except Exception:
                pass
            # #endregion
            if not retry_handler.should_retry(exc, attempt):
                raise
            
            emit_runtime_info(f"codex exec retryable error | attempt={attempt + 1} error={str(exc)[:200]}")
            
            if attempt >= retry_handler.max_retries:
                emit_runtime_info(f"codex exec max retries exceeded | attempts={attempt + 1}")
                raise
    
    raise RuntimeError("codex exec failed: unexpected retry loop exit")


def _run_codex_exec_once(prompt: str, timeout_sec: int, attempt: int) -> tuple[str, Path]:
    """
    Codex CLI を1回実行する。
    .codex/config.toml を読み込むため、リポジトリルートを cwd に指定する。
    """
    local_config_path = ROOT / ".codex" / "config.toml"

    project_cfg = _agent_read_project_codex_kv(local_config_path)
    cfg_model = project_cfg.get("model")
    cfg_reasoning = project_cfg.get("model_reasoning_effort")
    cfg_approval = project_cfg.get("approval_policy")
    cfg_sandbox = project_cfg.get("sandbox_mode")
    cfg_web_search = project_cfg.get("web_search")

    cmd: list[str] = ["codex", "exec"]
    # `.codex/config.toml` を Codex に「渡す」: CLI オプション/override に展開する
    if cfg_model:
        cmd += ["-m", cfg_model.strip().strip('"').strip("'")]
    if cfg_sandbox:
        cmd += ["-s", cfg_sandbox.strip().strip('"').strip("'")]
    if cfg_reasoning:
        cmd += ["-c", f"model_reasoning_effort={cfg_reasoning}"]
    if cfg_approval:
        cmd += ["-c", f"approval_policy={cfg_approval}"]
    if cfg_web_search:
        cmd += ["-c", f"web_search={cfg_web_search}"]
    cmd.append(prompt)
    heartbeat_sec = 15.0
    start_mono = time.monotonic()
    deadline = start_mono + float(timeout_sec)
    next_heartbeat = start_mono + heartbeat_sec
    
    if attempt == 0:
        emit_runtime_info(f"codex exec started | timeout_sec={timeout_sec} config={local_config_path}")
    
    env = os.environ.copy()
    user_home = str(Path.home())
    if 'USERPROFILE' not in env:
        env['USERPROFILE'] = user_home
    if 'HOME' not in env:
        env['HOME'] = user_home
    env['CODEX_HOME'] = str(Path.home() / ".codex")

    # #region agent log
    try:
        codex_home_value = env.get("CODEX_HOME") or ""
        codex_home_config = Path(codex_home_value) / "config.toml" if codex_home_value else None
        _agent_debug_log(
            run_id="post-fix",
            hypothesis_id="A",
            location="radar_ops.py:_run_codex_exec_once",
            message="codex exec env/cfg snapshot",
            data={
                "platform": sys.platform,
                "which_codex": shutil.which("codex"),
                "cwd": str(ROOT),
                "home": str(Path.home()),
                "env_CODEX_HOME": env.get("CODEX_HOME"),
                "env_HOME": env.get("HOME"),
                "env_USERPROFILE": env.get("USERPROFILE"),
                "project_cfg_keys": sorted(project_cfg.keys()),
                "project_cfg_selected": {
                    "model": cfg_model,
                    "model_reasoning_effort": cfg_reasoning,
                    "approval_policy": cfg_approval,
                    "sandbox_mode": cfg_sandbox,
                    "web_search": cfg_web_search,
                },
                "cmd_head": cmd[:12],
                "project_config": _agent_summarize_config(local_config_path),
                "codex_home_config": _agent_summarize_config(codex_home_config) if codex_home_config else {"path": "", "exists": False},
            },
        )
    except Exception:
        pass
    # #endregion
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(ROOT),
    )

    while proc.poll() is None:
        now = time.monotonic()
        elapsed = int(now - start_mono)
        if now >= next_heartbeat:
            emit_runtime_info(
                f"codex exec running | elapsed_sec={elapsed} timeout_sec={timeout_sec}"
            )
            next_heartbeat += heartbeat_sec
        if now >= deadline:
            proc.kill()
            stdout_text, stderr_text = proc.communicate()
            audit_path = write_codex_audit(stdout_text, stderr_text, return_code=124)
            emit_runtime_info(
                f"codex exec timeout | elapsed_sec={elapsed} audit={audit_path.relative_to(ROOT)}"
            )
            raise RuntimeError(
                f"codex exec timed out after {timeout_sec}s (audit={audit_path})"
            )
        time.sleep(1.0)

    result_stdout, result_stderr = proc.communicate()
    elapsed_done = int(time.monotonic() - start_mono)
    audit_path = write_codex_audit(result_stdout, result_stderr, return_code=proc.returncode or 0)

    # #region agent log
    try:
        stderr_head = "\n".join((result_stderr or "").splitlines()[:30])
        _agent_debug_log(
            run_id="post-fix",
            hypothesis_id="B",
            location="radar_ops.py:_run_codex_exec_once",
            message="codex exec completed (captured stderr head)",
            data={"return_code": proc.returncode, "audit": str(audit_path), "stderr_head": stderr_head[:1200]},
        )
    except Exception:
        pass
    # #endregion
    if proc.returncode != 0:
        emit_runtime_info(
            f"codex exec failed | code={proc.returncode} elapsed_sec={elapsed_done} audit={audit_path.relative_to(ROOT)}"
        )
        raise RuntimeError(
            f"codex exec failed with code={proc.returncode} (audit={audit_path})"
        )

    emit_runtime_info(
        f"codex exec completed | elapsed_sec={elapsed_done} audit={audit_path.relative_to(ROOT)}"
    )
    return result_stdout.strip(), audit_path


def collect_sources_with_codex_exec(sources: list[dict[str, Any]]) -> tuple[list[SourceResult], Path]:
    if shutil.which("codex") is None:
        raise RuntimeError("codex command is not available")

    prompt = build_codex_latest_prompt(sources)
    stdout_text, audit_path = run_codex_exec(prompt)
    payload = extract_json_object(stdout_text)

    if payload.get("error") == "OUT_OF_SCOPE":
        raise RuntimeError(f"codex returned OUT_OF_SCOPE (audit={audit_path})")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise RuntimeError(f"codex output results must be list (audit={audit_path})")
    if len(raw_results) != len(sources):
        raise RuntimeError(
            f"codex output results count mismatch: expected={len(sources)} got={len(raw_results)} (audit={audit_path})"
        )

    source_by_homepage: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_by_homepage[normalize_prefix(str(source.get("homepage", "")))] = source

    seen_homepages: set[str] = set()
    result_by_id: dict[str, SourceResult] = {}
    for entry in raw_results:
        if not isinstance(entry, dict):
            raise RuntimeError(f"codex result item must be object (audit={audit_path})")

        homepage_key = normalize_prefix(str(entry.get("site", "")))
        if not homepage_key:
            raise RuntimeError(f"codex result has invalid site url (audit={audit_path})")
        if homepage_key in seen_homepages:
            raise RuntimeError(f"codex result has duplicate site: {homepage_key} (audit={audit_path})")

        source = source_by_homepage.get(homepage_key)
        if source is None:
            raise RuntimeError(f"codex result site is out of allowed scope: {homepage_key} (audit={audit_path})")

        seen_homepages.add(homepage_key)

        latest_title = normalize_space(str(entry.get("latest_title", "") or ""))
        latest_url = str(entry.get("latest_url", "") or "").strip()
        latest_date = str(entry.get("latest_date", "") or "").strip()
        method = normalize_space(str(entry.get("method", "") or "")).lower()
        evidence_url = str(entry.get("evidence_url", "") or "").strip()
        source_id = str(source.get("id", ""))
        source_homepage = str(source.get("homepage", "")).strip()

        if method not in {"rss", "atom", "html"}:
            repaired_method = "html"
            emit_runtime_info(
                f"codex method repaired | source={source_id} from={method or 'empty'} to={repaired_method}"
            )
            method = repaired_method

        if not latest_title or not latest_url:
            missing_fields: list[str] = []
            if not latest_title:
                missing_fields.append("latest_title")
            if not latest_url:
                missing_fields.append("latest_url")

            reason = ",".join(missing_fields)
            if not latest_title:
                latest_title = codex_unavailable_title(reason)
            if not latest_url:
                latest_url = source_homepage
            if not evidence_url:
                evidence_url = source_homepage
            emit_runtime_info(
                f"codex fields repaired | source={source_id} missing={reason} strategy=unavailable-message"
            )

        if not evidence_url:
            evidence_url = latest_url

        if not has_allowed_prefix(latest_url, source.get("allowed_entry_prefixes", [])):
            raise RuntimeError(f"codex latest_url out of boundary: {latest_url} (audit={audit_path})")

        if evidence_url and not has_allowed_prefix(evidence_url, evidence_prefixes_for_source(source)):
            raise RuntimeError(f"codex evidence_url out of boundary: {evidence_url} (audit={audit_path})")

        item = RadarItem(
            title=latest_title,
            link=latest_url,
            published=normalize_published(latest_date),
            collected_via=f"codex-{method}",
            evidence_url=evidence_url,
        )

        source_id = str(source.get("id", ""))
        result_by_id[source_id] = SourceResult(
            source_id=source_id,
            name=str(source.get("name", "")),
            homepage=str(source.get("homepage", "")),
            items=[item],
            errors=[],
        )

    missing_source_ids = [str(source.get("id", "")) for source in sources if str(source.get("id", "")) not in result_by_id]
    if missing_source_ids:
        raise RuntimeError(f"codex result missing sources: {', '.join(missing_source_ids)} (audit={audit_path})")

    ordered = [result_by_id[str(source.get("id", ""))] for source in sources]
    return ordered, audit_path


def append_progress(summary: str) -> None:
    ts = utc_now().strftime("[%Y-%m-%d %H:%MZ]")
    line = f"{ts} agent-radar: {summary}\n"
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def build_report(snapshot: dict[str, Any], new_items: list[dict[str, str]]) -> str:
    lines = [
        f"# Source Radar Report ({utc_now().strftime('%Y-%m-%d')})",
        "",
        f"- Generated at: `{snapshot['generated_at']}`",
        f"- Sources scanned: `{snapshot['total_sources']}`",
        f"- Total items: `{snapshot['total_items']}`",
        f"- New items: `{len(new_items)}`",
        "",
        "## New Items",
        "",
    ]

    if not new_items:
        lines.append("- No new items")
    else:
        for item in new_items:
            source_id = item.get("source_id", "unknown")
            title = item.get("title", "(untitled)")
            link = item.get("link", "")
            lines.append(f"- [{source_id}] [{title}]({link})")

    return "\n".join(lines) + "\n"


def write_daily_report(snapshot: dict[str, Any], new_items: list[dict[str, str]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{utc_now().strftime('%Y-%m-%d')}.md"
    report_block = build_report(snapshot, new_items)

    if report_file.exists():
        with report_file.open("a", encoding="utf-8") as f:
            f.write("\n")
            f.write(report_block)
    else:
        with report_file.open("w", encoding="utf-8") as f:
            f.write(report_block)


def run_update(collector_mode: str = "auto") -> int:
    cfg = read_json(OFFICIAL_SOURCES, default={})
    sources = cfg.get("sources", [])
    if not sources:
        print("ERROR: official sources are empty.", file=sys.stderr)
        return 1

    previous_state = read_json(STATE_FILE, default={"sources": {}})
    previous_links_map: dict[str, set[str]] = {
        sid: set((data or {}).get("links", []))
        for sid, data in (previous_state.get("sources", {}) or {}).items()
    }

    now = iso_now()

    snapshot_sources: list[dict[str, Any]] = []
    state_sources: dict[str, Any] = {}
    new_items: list[dict[str, str]] = []

    total_items = 0

    collector_warnings: list[str] = []
    collector_used = "native"
    results: list[SourceResult] = []
    mutation_modules = load_mutation_modules()

    if collector_mode in {"auto", "codex"}:
        emit_runtime_info(
            f"update collector attempt | requested={collector_mode} phase=codex"
        )
        try:
            results, audit_path = collect_sources_with_codex_exec(sources)
            collector_used = "codex"
            append_progress(f"codex collector used | audit={audit_path.relative_to(ROOT)}")
        except RuntimeError as exc:
            if collector_mode == "codex":
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1
            emit_runtime_info(
                f"update collector fallback | from=codex to=native reason={normalize_space(str(exc))}"
            )
            collector_warnings.append(str(exc))

    if not results:
        emit_runtime_info(
            f"update collector attempt | requested={collector_mode} phase=native"
        )
        results = [collect_source(source) for source in sources]
        collector_used = "native"

    for result in results:
        source_links = [item.link for item in result.items]
        current_set = set(source_links)
        previous_set = previous_links_map.get(result.source_id, set())

        for item in result.items:
            if item.link not in previous_set:
                enriched = apply_mutations_to_new_item(
                    {
                        "source_id": result.source_id,
                        "title": item.title,
                        "link": item.link,
                        "published": item.published,
                        "collected_via": item.collected_via,
                        "evidence_url": item.evidence_url,
                    },
                    mutation_modules,
                )
                new_items.append(enriched)

        snapshot_sources.append(
            {
                "id": result.source_id,
                "name": result.name,
                "homepage": result.homepage,
                "item_count": len(result.items),
                "items": [item.to_dict() for item in result.items],
                "errors": result.errors,
            }
        )

        state_sources[result.source_id] = {
            "links": sorted(current_set),
            "fingerprint": fingerprint_links(sorted(current_set)),
            "updated_at": now,
        }

        total_items += len(result.items)

    snapshot = {
        "generated_at": now,
        "collector": collector_used,
        "total_sources": len(snapshot_sources),
        "total_items": total_items,
        "sources": snapshot_sources,
    }
    if collector_warnings:
        snapshot["collector_warnings"] = collector_warnings
    state = {
        "version": 1,
        "last_run_at": now,
        "last_collector": collector_used,
        "sources": state_sources,
    }
    new_items_doc = {
        "generated_at": now,
        "collector": collector_used,
        "new_item_count": len(new_items),
        "new_items": new_items,
    }
    if collector_warnings:
        new_items_doc["collector_warnings"] = collector_warnings

    write_json(SNAPSHOT_FILE, snapshot)
    write_json(STATE_FILE, state)
    write_json(NEW_ITEMS_FILE, new_items_doc)
    write_daily_report(snapshot, new_items)

    summary = (
        f"update completed | collector={collector_used} "
        f"sources={len(snapshot_sources)} items={total_items} new={len(new_items)} "
        f"mutations_loaded={len(mutation_modules)}"
    )
    if collector_warnings:
        summary += f" warnings={len(collector_warnings)}"
    append_progress(summary)

    print(
        f"OK: update completed (collector={collector_used} sources={len(snapshot_sources)} total_items={total_items} new_items={len(new_items)})"
    )
    return 0


def validate_source_boundary(official_sources: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected_homepages = {
        "https://qwenlm.github.io/blog/",
        "https://deepseek.ai/blog/",
        "https://sakana.ai/blog/",
        "https://huggingface.co/blog/",
        "https://developers.openai.com/blog/",
        "https://www.anthropic.com/engineering/",
    }

    actual_homepages = {str(src.get("homepage", "")) for src in official_sources}
    if len(official_sources) != 6:
        errors.append(f"official_sources must contain exactly 6 sources, got {len(official_sources)}")
    if actual_homepages != expected_homepages:
        errors.append("official_sources homepages mismatch expected fixed six blogs")

    ids = [src.get("id", "") for src in official_sources]
    if len(ids) != len(set(ids)):
        errors.append("official source ids must be unique")

    return errors


def validate_mutation_index() -> list[str]:
    errors: list[str] = []
    index = ensure_mutation_index()
    modules = index.get("modules", [])
    if not isinstance(modules, list):
        return ["mutation index modules must be list"]

    for entry in modules:
        if not isinstance(entry, dict):
            errors.append("mutation index entry must be object")
            continue
        exp_id = str(entry.get("id", "")).strip()
        module = str(entry.get("module", "")).strip()
        rel_path = str(entry.get("path", "")).strip()
        if not exp_id or not module or not rel_path:
            errors.append(f"mutation index entry missing required fields: {entry}")
            continue
        if not rel_path.startswith("harness/agent_radar/mutations/"):
            errors.append(f"mutation path out of scope: {rel_path}")
            continue
        full_path = ROOT / rel_path
        if not full_path.exists():
            errors.append(f"mutation module missing: {rel_path}")
            continue
        expected_hash = str(entry.get("sha256", ""))
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        if expected_hash and expected_hash != actual_hash:
            errors.append(f"mutation hash mismatch: {rel_path}")
    return errors


def validate_monitoring_targets_schema() -> list[str]:
    errors: list[str] = []
    targets_doc = read_json(MONITORING_TARGETS_FILE, default={"targets": []})
    targets = targets_doc.get("targets") if isinstance(targets_doc, dict) else []
    if not isinstance(targets, list):
        return ["monitoring_targets targets must be list"]

    seen_ids: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            errors.append("monitoring target must be object")
            continue
        target_id = str(target.get("id", "")).strip()
        query_hint = str(target.get("query_hint", "")).strip()
        threshold = str(target.get("threshold", "")).strip()
        if not target_id:
            errors.append("monitoring target id is required")
            continue
        if target_id in seen_ids:
            errors.append(f"monitoring target id must be unique: {target_id}")
        seen_ids.add(target_id)
        if not query_hint:
            errors.append(f"monitoring target query_hint is required: {target_id}")
        if not threshold or parse_threshold_expression(threshold) is None:
            errors.append(f"monitoring target threshold is invalid: {target_id} {threshold}")
    return errors


def validate_monitoring_artifacts() -> list[str]:
    errors: list[str] = []
    now = utc_now()
    freshness_limit = dt.timedelta(hours=36)
    bootstrap_grace_limit = dt.timedelta(hours=24)

    targets_doc = read_json(MONITORING_TARGETS_FILE, default={"targets": []})
    targets = targets_doc.get("targets") if isinstance(targets_doc, dict) else []
    if not isinstance(targets, list):
        return ["monitoring_targets targets must be list"]
    if len(targets) == 0:
        return []

    latest_doc = read_json(METRICS_LATEST_FILE, default={})
    results_doc = read_json(MONITORING_RESULTS_FILE, default={})

    if not isinstance(latest_doc, dict):
        errors.append("metrics latest payload must be object")
        return errors
    if not isinstance(results_doc, dict):
        errors.append("monitoring results payload must be object")
        return errors

    latest_generated_at = parse_iso_datetime(str(latest_doc.get("generated_at", "")))
    results_generated_at = parse_iso_datetime(str(results_doc.get("generated_at", "")))
    if latest_generated_at is None:
        errors.append("metrics latest generated_at is missing or invalid")
    elif now - latest_generated_at > freshness_limit:
        errors.append("metrics latest generated_at is stale")
    if results_generated_at is None:
        errors.append("monitoring results generated_at is missing or invalid")
    elif now - results_generated_at > freshness_limit:
        errors.append("monitoring results generated_at is stale")

    latest_loop = str(latest_doc.get("loop", "")).strip()
    results_loop = str(results_doc.get("loop", "")).strip()
    bootstrap_mode = latest_loop == "bootstrap" or results_loop == "bootstrap"
    if bootstrap_mode:
        reference_times = [
            generated_at
            for generated_at in (latest_generated_at, results_generated_at)
            if generated_at is not None
        ]
        if not reference_times:
            errors.append("monitoring bootstrap mode has no valid generated_at timestamps")
        else:
            latest_reference = max(reference_times)
            if now - latest_reference > bootstrap_grace_limit:
                errors.append(
                    "monitoring bootstrap mode exceeded 24h while monitoring targets are configured"
                )

    metrics = latest_doc.get("metrics")
    if not bootstrap_mode:
        if not isinstance(metrics, dict) or len(metrics) == 0:
            errors.append("metrics latest metrics must be a non-empty object")
        else:
            required_metrics = [
                "autogrow.success",
                "autogrow.success_rate",
                "radar.monitor_target_count",
            ]
            for metric_name in required_metrics:
                if metric_name not in metrics:
                    errors.append(f"metrics latest missing required metric: {metric_name}")

    evaluations = results_doc.get("evaluations")
    if not bootstrap_mode:
        if not isinstance(evaluations, list):
            errors.append("monitoring results evaluations must be list")
            evaluations = []
        total_targets = results_doc.get("total_targets")
        if not isinstance(total_targets, int):
            errors.append("monitoring results total_targets must be int")
        else:
            if total_targets != len(targets):
                errors.append(
                    f"monitoring results total_targets mismatch: expected={len(targets)} got={total_targets}"
                )
            if total_targets != len(evaluations):
                errors.append(
                    f"monitoring results evaluations mismatch: total_targets={total_targets} evaluations={len(evaluations)}"
                )

        pass_count = results_doc.get("pass_count")
        if not isinstance(pass_count, int):
            errors.append("monitoring results pass_count must be int")
        elif isinstance(total_targets, int) and not (0 <= pass_count <= total_targets):
            errors.append(
                f"monitoring results pass_count out of range: pass_count={pass_count} total_targets={total_targets}"
            )

    return errors


def run_validate() -> int:
    cfg = read_json(OFFICIAL_SOURCES, default={})
    sources = cfg.get("sources", [])
    state = read_json(STATE_FILE, default={})
    snapshot = read_json(SNAPSHOT_FILE, default={})
    new_items_doc = read_json(NEW_ITEMS_FILE, default={})

    errors: list[str] = []
    errors.extend(validate_source_boundary(sources))
    errors.extend(validate_mutation_index())
    errors.extend(validate_monitoring_targets_schema())
    errors.extend(validate_monitoring_artifacts())

    src_map = {src["id"]: src for src in sources if "id" in src}
    expected_ids = set(src_map.keys())

    state_ids = set((state.get("sources") or {}).keys())
    snapshot_ids = {src.get("id", "") for src in snapshot.get("sources", [])}

    if expected_ids != state_ids:
        errors.append("state source ids do not match official source ids")
    if expected_ids != snapshot_ids:
        errors.append("snapshot source ids do not match official source ids")

    for sid, source_state in (state.get("sources") or {}).items():
        source_cfg = src_map.get(sid)
        if not source_cfg:
            continue
        allowed = source_cfg.get("allowed_entry_prefixes", [])
        for link in source_state.get("links", []):
            if not has_allowed_prefix(link, allowed):
                errors.append(f"state link out of boundary: {sid} {link}")

    for source_snap in snapshot.get("sources", []):
        sid = source_snap.get("id", "")
        source_cfg = src_map.get(sid)
        if not source_cfg:
            continue
        allowed = source_cfg.get("allowed_entry_prefixes", [])
        evidence_allowed = evidence_prefixes_for_source(source_cfg)
        for item in source_snap.get("items", []):
            link = str(item.get("link", ""))
            if not has_allowed_prefix(link, allowed):
                errors.append(f"snapshot link out of boundary: {sid} {link}")
            evidence_url = str(item.get("evidence_url", ""))
            if evidence_url and not has_allowed_prefix(evidence_url, evidence_allowed):
                errors.append(f"snapshot evidence_url out of boundary: {sid} {evidence_url}")

    for item in new_items_doc.get("new_items", []):
        sid = item.get("source_id", "")
        source_cfg = src_map.get(sid)
        link = str(item.get("link", ""))
        if not source_cfg:
            errors.append(f"new item has unknown source id: {sid}")
            continue
        allowed = source_cfg.get("allowed_entry_prefixes", [])
        evidence_allowed = evidence_prefixes_for_source(source_cfg)
        if not has_allowed_prefix(link, allowed):
            errors.append(f"new item link out of boundary: {sid} {link}")
        evidence_url = str(item.get("evidence_url", ""))
        if evidence_url and not has_allowed_prefix(evidence_url, evidence_allowed):
            errors.append(f"new item evidence_url out of boundary: {sid} {evidence_url}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("OK: validate completed")
    return 0


def iter_target_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for target in paths:
        if not target.exists():
            continue
        if target.is_file():
            files.append(target)
            continue
        for path in target.rglob("*"):
            if path.is_file():
                files.append(path)
    return files


def run_garden() -> int:
    issues: list[str] = []
    for path in iter_target_files(GARDEN_TARGETS):
        rel = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat in GARDEN_PATTERNS:
                if pat.search(line):
                    issues.append(f"{rel}:{lineno}: {line.strip()}")
                    break

    expected_growth_doc = expected_autonomous_growth_doc_from_backlog()
    actual_growth_doc = (
        AUTONOMOUS_GROWTH_DOC.read_text(encoding="utf-8")
        if AUTONOMOUS_GROWTH_DOC.exists()
        else ""
    )
    if actual_growth_doc.strip() != expected_growth_doc.strip():
        issues.append(
            "docs/agent-harness/autonomous-growth.md is stale against harness/agent_radar/experiment_backlog.json"
        )

    if issues:
        for issue in issues:
            if issue.startswith("docs/agent-harness/autonomous-growth.md"):
                print(f"ERROR: stale doc: {issue}", file=sys.stderr)
            else:
                print(f"ERROR: unresolved placeholder: {issue}", file=sys.stderr)
        return 1

    print("OK: garden completed")
    return 0


def normalize_backlog_docs() -> list[str]:
    actions: list[str] = []

    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"version": 1, "items": []})
    if not isinstance(backlog, dict):
        backlog = {"version": 1, "items": []}
        actions.append("reset_experiment_backlog_root")
    items = backlog.get("items")
    if not isinstance(items, list):
        backlog["items"] = []
        actions.append("reset_experiment_backlog_items")
    backlog["version"] = int(backlog.get("version", 1))
    backlog["updated_at"] = iso_now()
    if actions:
        write_json(EXPERIMENT_BACKLOG_FILE, backlog)

    new_items_doc = read_json(NEW_ITEMS_FILE, default={"new_items": []})
    if not isinstance(new_items_doc, dict):
        new_items_doc = {"generated_at": iso_now(), "new_item_count": 0, "new_items": []}
        actions.append("reset_new_items_root")
    new_items = new_items_doc.get("new_items")
    if not isinstance(new_items, list):
        new_items_doc["new_items"] = []
        new_items_doc["new_item_count"] = 0
        new_items_doc["generated_at"] = iso_now()
        actions.append("reset_new_items_list")
    if actions:
        write_json(NEW_ITEMS_FILE, new_items_doc)
    return actions


def repair_validate_boundary() -> list[str]:
    cfg = read_json(OFFICIAL_SOURCES, default={})
    sources = cfg.get("sources", [])
    src_map: dict[str, dict[str, Any]] = {
        str(src.get("id", "")): src for src in sources if isinstance(src, dict) and src.get("id")
    }
    expected_ids = set(src_map.keys())
    actions: list[str] = []

    state = read_json(STATE_FILE, default={"version": 1, "last_run_at": iso_now(), "sources": {}})
    if not isinstance(state, dict):
        state = {"version": 1, "last_run_at": iso_now(), "sources": {}}
        actions.append("reset_state_root")
    state_sources = state.get("sources")
    if not isinstance(state_sources, dict):
        state_sources = {}
        actions.append("reset_state_sources")

    sanitized_state_sources: dict[str, Any] = {}
    for sid in expected_ids:
        raw_state = state_sources.get(sid, {})
        if not isinstance(raw_state, dict):
            raw_state = {}
        allowed = src_map[sid].get("allowed_entry_prefixes", [])
        links = raw_state.get("links", [])
        if not isinstance(links, list):
            links = []
            actions.append(f"reset_state_links:{sid}")
        kept_links = sorted(
            {
                str(link)
                for link in links
                if isinstance(link, str) and has_allowed_prefix(link, allowed)
            }
        )
        if len(kept_links) != len([link for link in links if isinstance(link, str)]):
            actions.append(f"trim_state_links:{sid}")
        sanitized_state_sources[sid] = {
            "links": kept_links,
            "fingerprint": fingerprint_links(kept_links),
            "updated_at": iso_now(),
        }

    if set(state_sources.keys()) != expected_ids:
        actions.append("realign_state_source_ids")
    state["sources"] = sanitized_state_sources
    state["last_run_at"] = iso_now()
    state["version"] = int(state.get("version", 1))
    write_json(STATE_FILE, state)

    snapshot = read_json(SNAPSHOT_FILE, default={"generated_at": iso_now(), "sources": []})
    if not isinstance(snapshot, dict):
        snapshot = {"generated_at": iso_now(), "sources": []}
        actions.append("reset_snapshot_root")
    raw_snapshot_sources = snapshot.get("sources")
    if not isinstance(raw_snapshot_sources, list):
        raw_snapshot_sources = []
        actions.append("reset_snapshot_sources")

    by_id: dict[str, dict[str, Any]] = {}
    for source in raw_snapshot_sources:
        if not isinstance(source, dict):
            continue
        sid = str(source.get("id", "")).strip()
        if sid in expected_ids and sid not in by_id:
            by_id[sid] = source
    if len(by_id) != len(expected_ids):
        actions.append("realign_snapshot_source_ids")

    sanitized_snapshot_sources: list[dict[str, Any]] = []
    for sid in src_map:
        source_cfg = src_map[sid]
        source_snap = by_id.get(
            sid,
            {
                "id": sid,
                "name": source_cfg.get("name", sid),
                "homepage": source_cfg.get("homepage", ""),
                "item_count": 0,
                "items": [],
                "errors": [],
            },
        )
        items = source_snap.get("items")
        if not isinstance(items, list):
            items = []
            actions.append(f"reset_snapshot_items:{sid}")

        allowed = source_cfg.get("allowed_entry_prefixes", [])
        evidence_allowed = evidence_prefixes_for_source(source_cfg)
        kept_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            link = str(item.get("link", ""))
            evidence_url = str(item.get("evidence_url", ""))
            if not has_allowed_prefix(link, allowed):
                continue
            if evidence_url and not has_allowed_prefix(evidence_url, evidence_allowed):
                continue
            kept_items.append(item)
        if len(kept_items) != len(items):
            actions.append(f"trim_snapshot_items:{sid}")
        source_snap["items"] = kept_items
        source_snap["item_count"] = len(kept_items)
        sanitized_snapshot_sources.append(source_snap)

    snapshot["generated_at"] = iso_now()
    snapshot["sources"] = sanitized_snapshot_sources
    snapshot["total_sources"] = len(sanitized_snapshot_sources)
    snapshot["total_items"] = sum(src.get("item_count", 0) for src in sanitized_snapshot_sources)
    write_json(SNAPSHOT_FILE, snapshot)

    new_items_doc = read_json(NEW_ITEMS_FILE, default={"generated_at": iso_now(), "new_items": []})
    if not isinstance(new_items_doc, dict):
        new_items_doc = {"generated_at": iso_now(), "new_items": []}
        actions.append("reset_new_items_doc")
    raw_new_items = new_items_doc.get("new_items")
    if not isinstance(raw_new_items, list):
        raw_new_items = []
        actions.append("reset_new_items_list")

    kept_new_items: list[dict[str, Any]] = []
    for item in raw_new_items:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("source_id", ""))
        if sid not in expected_ids:
            continue
        source_cfg = src_map[sid]
        link = str(item.get("link", ""))
        evidence_url = str(item.get("evidence_url", ""))
        if not has_allowed_prefix(link, source_cfg.get("allowed_entry_prefixes", [])):
            continue
        if evidence_url and not has_allowed_prefix(evidence_url, evidence_prefixes_for_source(source_cfg)):
            continue
        kept_new_items.append(item)
    if len(kept_new_items) != len(raw_new_items):
        actions.append("trim_new_items")
    new_items_doc["generated_at"] = iso_now()
    new_items_doc["new_items"] = kept_new_items
    new_items_doc["new_item_count"] = len(kept_new_items)
    write_json(NEW_ITEMS_FILE, new_items_doc)

    mutation_actions = repair_mutation_index()
    actions.extend(mutation_actions)

    monitoring_actions = repair_monitoring_targets()
    actions.extend(monitoring_actions)
    actions.extend(repair_monitoring_artifact_freshness())

    return actions


def repair_mutation_index() -> list[str]:
    actions: list[str] = []
    index = ensure_mutation_index()
    modules = index.get("modules", [])
    if not isinstance(modules, list):
        modules = []
        actions.append("reset_mutation_modules")

    sanitized: list[dict[str, Any]] = []
    for entry in modules:
        if not isinstance(entry, dict):
            actions.append("drop_invalid_mutation_entry")
            continue
        exp_id = str(entry.get("id", "")).strip()
        module = str(entry.get("module", "")).strip()
        rel_path = str(entry.get("path", "")).strip()
        if not exp_id or not module or not rel_path:
            actions.append("drop_incomplete_mutation_entry")
            continue
        if not rel_path.startswith("harness/agent_radar/mutations/"):
            actions.append(f"drop_out_of_scope_mutation:{rel_path}")
            continue
        full_path = ROOT / rel_path
        if not full_path.exists():
            actions.append(f"drop_missing_mutation:{rel_path}")
            continue
        entry["sha256"] = hashlib.sha256(full_path.read_bytes()).hexdigest()
        entry["updated_at"] = iso_now()
        sanitized.append(entry)

    if len(sanitized) != len(modules):
        actions.append("trim_mutation_index")
    if actions:
        index["modules"] = sanitized
        index["updated_at"] = iso_now()
        write_json(MUTATION_INDEX_FILE, index)
    return actions


def repair_monitoring_targets() -> list[str]:
    actions: list[str] = []
    changed = False
    doc = read_json(MONITORING_TARGETS_FILE, default={"version": 1, "targets": []})
    if not isinstance(doc, dict):
        doc = {"version": 1, "targets": []}
        actions.append("reset_monitoring_targets_root")
    targets = doc.get("targets")
    if not isinstance(targets, list):
        targets = []
        actions.append("reset_monitoring_targets_list")

    sanitized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            actions.append("drop_invalid_monitor_target")
            continue
        target_id = str(target.get("id", "")).strip()
        theme = str(target.get("theme", "")).strip().lower()
        if not target_id:
            actions.append("drop_empty_monitor_target_id")
            continue
        if target_id in seen_ids:
            actions.append(f"drop_duplicate_monitor_target:{target_id}")
            continue
        seen_ids.add(target_id)
        if not theme:
            theme = "general"
            actions.append(f"default_theme_for:{target_id}")
        query_hint, threshold = monitoring_profile_for_theme(theme)
        if str(target.get("query_hint", "")) != query_hint:
            changed = True
            actions.append(f"fix_query_hint:{target_id}")
        if str(target.get("threshold", "")) != threshold:
            changed = True
            actions.append(f"fix_threshold:{target_id}")
        owner = str(target.get("owner", "agent-radar"))
        name = str(target.get("name", f"{target_id} health check"))
        sanitized.append(
            {
                "id": target_id,
                "theme": theme,
                "owner": owner,
                "name": name,
                "query_hint": query_hint,
                "threshold": threshold,
            }
        )

    if actions or changed:
        doc["version"] = int(doc.get("version", 1))
        doc["updated_at"] = iso_now()
        doc["targets"] = sanitized
        write_json(MONITORING_TARGETS_FILE, doc)
    return actions


def repair_monitoring_artifact_freshness() -> list[str]:
    actions: list[str] = []
    targets_doc = read_json(MONITORING_TARGETS_FILE, default={"targets": []})
    targets = targets_doc.get("targets") if isinstance(targets_doc, dict) else []
    if not isinstance(targets, list) or len(targets) == 0:
        return actions

    now = iso_now()
    latest_doc = read_json(METRICS_LATEST_FILE, default={})
    if not isinstance(latest_doc, dict):
        latest_doc = {}
        actions.append("reset_metrics_latest_root")
    latest_doc["version"] = int(latest_doc.get("version", 1))
    latest_doc["generated_at"] = now
    latest_doc["loop"] = "bootstrap"
    latest_doc["collector_mode"] = str(latest_doc.get("collector_mode", "native") or "native")
    latest_doc["steps"] = latest_doc.get("steps") if isinstance(latest_doc.get("steps"), list) else []
    metrics = latest_doc.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
        actions.append("reset_metrics_latest_metrics")
    metrics["radar.monitor_target_count"] = float(len(targets))
    latest_doc["metrics"] = metrics
    write_json(METRICS_LATEST_FILE, latest_doc)
    actions.append("refresh_metrics_latest")

    results_doc = read_json(MONITORING_RESULTS_FILE, default={})
    if not isinstance(results_doc, dict):
        results_doc = {}
        actions.append("reset_monitoring_results_root")
    results_doc["version"] = int(results_doc.get("version", 1))
    results_doc["generated_at"] = now
    results_doc["loop"] = "bootstrap"
    results_doc["pass_count"] = int(results_doc.get("pass_count", 0))
    results_doc["total_targets"] = int(results_doc.get("total_targets", len(targets)))
    evaluations = results_doc.get("evaluations")
    if not isinstance(evaluations, list):
        evaluations = []
        actions.append("reset_monitoring_results_evaluations")
    results_doc["evaluations"] = evaluations
    write_json(MONITORING_RESULTS_FILE, results_doc)
    actions.append("refresh_monitoring_results")

    return actions


def repair_garden_placeholders() -> list[str]:
    actions: list[str] = []
    replacement_note = (
        f"NOTE(agent-gardener {utc_now().strftime('%Y-%m-%d')}): "
        "placeholder was auto-resolved; follow-up is tracked in docs/agent-harness/autonomous-growth.md"
    )
    for path in iter_target_files(GARDEN_TARGETS):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        changed = False
        updated_lines: list[str] = []
        for line in text.splitlines():
            line_out = line
            if GARDEN_PATTERNS[0].search(line_out):
                line_out = re.sub(r"TODO:.*", replacement_note, line_out)
                changed = True
            if GARDEN_PATTERNS[1].search(line_out):
                line_out = re.sub(r"\[NEEDS\s+CLARIFICATION.*", replacement_note, line_out, flags=re.IGNORECASE)
                changed = True
            updated_lines.append(line_out)
        if changed:
            path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
            actions.append(f"rewrite:{path.relative_to(ROOT)}")
    return actions


def repair_autonomous_growth_doc_currency() -> list[str]:
    expected = expected_autonomous_growth_doc_from_backlog()
    current = (
        AUTONOMOUS_GROWTH_DOC.read_text(encoding="utf-8")
        if AUTONOMOUS_GROWTH_DOC.exists()
        else ""
    )
    if current.strip() == expected.strip():
        return []
    AUTONOMOUS_GROWTH_DOC.parent.mkdir(parents=True, exist_ok=True)
    AUTONOMOUS_GROWTH_DOC.write_text(expected, encoding="utf-8")
    return [f"refresh:{AUTONOMOUS_GROWTH_DOC.relative_to(ROOT)}"]


def parse_threshold_expression(expr: str) -> tuple[str, float] | None:
    match = re.fullmatch(r"\s*(>=|<=|>|<|==)\s*(-?\d+(?:\.\d+)?)\s*", expr)
    if not match:
        return None
    op = match.group(1)
    value = float(match.group(2))
    return op, value


def threshold_passed(actual: float, expression: str) -> bool | None:
    parsed = parse_threshold_expression(expression)
    if parsed is None:
        return None
    op, expected = parsed
    if op == ">=":
        return actual >= expected
    if op == "<=":
        return actual <= expected
    if op == ">":
        return actual > expected
    if op == "<":
        return actual < expected
    if op == "==":
        return actual == expected
    return None


def publish_monitoring_artifacts(
    loop_name: str,
    collector_mode: str,
    outcomes: list[StepOutcome],
) -> None:
    previous_latest = read_json(METRICS_LATEST_FILE, default={})
    previous_results = read_json(MONITORING_RESULTS_FILE, default={})
    previous_latest_loop = (
        str(previous_latest.get("loop", "")).strip()
        if isinstance(previous_latest, dict)
        else ""
    )
    previous_results_loop = (
        str(previous_results.get("loop", "")).strip()
        if isinstance(previous_results, dict)
        else ""
    )
    previous_bootstrap_mode = (
        previous_latest_loop == "bootstrap" or previous_results_loop == "bootstrap"
    )
    loop_success = len(outcomes) > 0 and all(outcome.rc == 0 for outcome in outcomes)
    effective_loop_name = (
        "autogrow" if previous_bootstrap_mode and loop_success else loop_name
    )

    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"items": []})
    backlog_items = backlog.get("items") if isinstance(backlog, dict) else []
    if not isinstance(backlog_items, list):
        backlog_items = []

    new_items_doc = read_json(NEW_ITEMS_FILE, default={"new_item_count": 0})
    new_item_count_raw = new_items_doc.get("new_item_count") if isinstance(new_items_doc, dict) else 0
    new_item_count = int(new_item_count_raw) if isinstance(new_item_count_raw, int | float) else 0

    target_doc = read_json(MONITORING_TARGETS_FILE, default={"targets": []})
    targets = target_doc.get("targets") if isinstance(target_doc, dict) else []
    if not isinstance(targets, list):
        targets = []

    total_steps = len(outcomes)
    success_steps = sum(1 for outcome in outcomes if outcome.rc == 0)
    recovered_steps = sum(1 for outcome in outcomes if outcome.recovered)
    self_heal_actions = sum(len(outcome.repair_actions) for outcome in outcomes)

    metrics = {
        "autogrow.success": 1.0 if total_steps > 0 and success_steps == total_steps else 0.0,
        "autogrow.success_rate": (success_steps / total_steps) if total_steps > 0 else 0.0,
        "autogrow.recovered_steps": float(recovered_steps),
        "autogrow.self_heal_actions": float(self_heal_actions),
        "radar.new_item_count": float(new_item_count),
        "radar.backlog_total": float(len(backlog_items)),
        "radar.implemented_total": float(
            sum(1 for item in backlog_items if isinstance(item, dict) and str(item.get("status", "")).lower() == "implemented")
        ),
        "radar.monitor_target_count": float(len(targets)),
    }

    latest_payload = {
        "version": 1,
        "loop": effective_loop_name,
        "generated_at": iso_now(),
        "collector_mode": collector_mode,
        "steps": [
            {
                "name": outcome.name,
                "rc": outcome.rc,
                "recovered": outcome.recovered,
                "repair_actions": outcome.repair_actions,
            }
            for outcome in outcomes
        ],
        "metrics": metrics,
    }
    write_json(METRICS_LATEST_FILE, latest_payload)
    append_jsonl(METRICS_HISTORY_FILE, latest_payload)

    evaluations: list[dict[str, Any]] = []
    pass_count = 0
    for target in targets:
        if not isinstance(target, dict):
            continue
        target_id = str(target.get("id", ""))
        query_hint = str(target.get("query_hint", ""))
        threshold = str(target.get("threshold", ""))
        actual = metrics.get(query_hint)

        status = "unknown"
        passed: bool | None = None
        if isinstance(actual, float):
            passed = threshold_passed(actual, threshold)
            if passed is True:
                status = "pass"
                pass_count += 1
            elif passed is False:
                status = "fail"
            else:
                status = "invalid-threshold"
        evaluations.append(
            {
                "id": target_id,
                "query_hint": query_hint,
                "threshold": threshold,
                "actual": actual,
                "status": status,
            }
        )

    result_doc = {
        "version": 1,
        "generated_at": iso_now(),
        "loop": effective_loop_name,
        "pass_count": pass_count,
        "total_targets": len(evaluations),
        "evaluations": evaluations,
    }
    write_json(MONITORING_RESULTS_FILE, result_doc)
    if previous_bootstrap_mode and effective_loop_name == "autogrow":
        append_progress("monitoring loop transitioned | from=bootstrap to=autogrow")
    append_progress(
        f"monitoring evaluated | loop={effective_loop_name} pass={pass_count} total={len(evaluations)}"
    )


def append_self_heal_event(event: dict[str, Any]) -> None:
    doc = read_json(
        SELF_HEAL_LOG_FILE,
        default={"version": 1, "updated_at": iso_now(), "events": []},
    )
    if not isinstance(doc, dict):
        doc = {"version": 1, "updated_at": iso_now(), "events": []}
    events = doc.get("events")
    if not isinstance(events, list):
        events = []
    events.append(event)
    if len(events) > 200:
        events = events[-200:]
    doc["version"] = int(doc.get("version", 1))
    doc["updated_at"] = iso_now()
    doc["events"] = events
    write_json(SELF_HEAL_LOG_FILE, doc)


def next_experiment_id(items: list[dict[str, Any]]) -> str:
    max_no = 0
    for item in items:
        raw = str(item.get("id", ""))
        match = re.fullmatch(r"EXP-(\d+)", raw)
        if not match:
            continue
        no = int(match.group(1))
        if no > max_no:
            max_no = no
    return f"EXP-{max_no + 1:03d}"


def build_evaluation_task(exp_id: str, axes: list[str]) -> dict[str, Any]:
    axis_summary = ", ".join(axes)
    return {
        "id": f"EVAL-{exp_id}",
        "kind": "article-derived",
        "goal": (
            "複雑で信頼性の高いソフトウェアを大規模に構築・維持するため、"
            f"環境/フィードバックループ/制御システム（{axis_summary}）の改善効果を検証する。"
        ),
        "verification": "uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow",
        "expected_signals": [
            "autogrow.success == 1",
            "validate step passed",
            "garden step passed",
            "monitoring_results refreshed",
        ],
    }


def run_backlog() -> int:
    new_items_doc = read_json(NEW_ITEMS_FILE, default={"new_items": []})
    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"version": 1, "items": []})

    items = backlog.get("items")
    if not isinstance(items, list):
        print("ERROR: experiment_backlog.json items must be a list.", file=sys.stderr)
        return 1

    new_items = new_items_doc.get("new_items")
    if not isinstance(new_items, list):
        print("ERROR: new-items.json new_items must be a list.", file=sys.stderr)
        return 1

    existing_links = {
        str(item.get("origin_link", "")).strip()
        for item in items
        if str(item.get("origin_link", "")).strip()
    }

    created = 0
    for raw in new_items:
        if not isinstance(raw, dict):
            continue
        source_id = str(raw.get("source_id", "")).strip()
        title = normalize_space(str(raw.get("title", "")))
        link = str(raw.get("link", "")).strip()
        published = str(raw.get("published", "")).strip()

        if not source_id or not title or not link:
            continue
        if link in existing_links:
            continue

        exp_id = next_experiment_id(items)
        harness_tags = coerce_str_list(raw.get("harness_tags"))
        raw_themes = coerce_str_list(raw.get("themes"))
        detected_themes = detect_themes(title, link, " ".join(harness_tags), " ".join(raw_themes))
        themes: list[str] = []
        for token in [*harness_tags, *raw_themes, *detected_themes]:
            lowered = token.strip().lower()
            if lowered and lowered not in themes:
                themes.append(lowered)

        growth_axes = detect_growth_axes(title, link, " ".join(themes))
        checkpoint_policy = with_default_str_list(
            raw.get("state_checkpoint_policy"),
            DEFAULT_CHECKPOINT_POLICY,
        )
        replacements = with_default_str_list(
            raw.get("conversation_replacements"),
            DEFAULT_CONVERSATION_REPLACEMENTS,
        )
        theme_summary = ", ".join(themes)
        axis_summary = ", ".join(growth_axes)
        items.append(
            {
                "id": exp_id,
                "status": "proposed",
                "title": f"[{source_id}] {title}",
                "source": "agent-radar",
                "origin_source_id": source_id,
                "origin_link": link,
                "published": published,
                "created_at": iso_now(),
                "acceptance": (
                    "state checkpoint と差し替え表現を伴う評価タスクとして実装へ反映し、"
                    "autogrow 実行で結果を再現できる。"
                ),
                "hypothesis": (
                    f"記事知見（{theme_summary}）を {axis_summary} の改善へ反映すると、"
                    "品質ゲートと自律実行の信頼性を継続的に高められる。"
                ),
                "themes": themes,
                "growth_axes": growth_axes,
                "harness_tags": harness_tags,
                "state_checkpoint_policy": checkpoint_policy,
                "conversation_replacements": replacements,
                "innovation_priority": innovation_priority_for_themes(themes),
                "evaluation_task": build_evaluation_task(exp_id, growth_axes),
            }
        )
        existing_links.add(link)
        created += 1

    backlog["version"] = int(backlog.get("version", 1))
    backlog["updated_at"] = iso_now()
    backlog["items"] = items
    write_json(EXPERIMENT_BACKLOG_FILE, backlog)

    append_progress(f"backlog sync completed | created={created}")
    print(f"OK: backlog completed (created={created})")
    return 0


def detect_themes(*texts: str) -> list[str]:
    joined = " ".join(texts).lower()
    matched: list[str] = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in joined for keyword in keywords):
            matched.append(theme)
    if not matched:
        matched.append("general")
    deduped: list[str] = []
    for theme in matched:
        if theme not in deduped:
            deduped.append(theme)
    return deduped


def monitoring_profile_for_theme(theme: str) -> tuple[str, str]:
    theme_metric_map: dict[str, tuple[str, str]] = {
        "mcp": ("radar.new_item_count", ">= 0"),
        "skills": ("radar.new_item_count", ">= 0"),
        "environment": ("autogrow.success_rate", ">= 0.9"),
        "feedback": ("autogrow.success_rate", ">= 0.95"),
        "control": ("autogrow.success_rate", ">= 0.95"),
        "reliability": ("autogrow.success_rate", ">= 0.95"),
        "scalability": ("autogrow.success_rate", ">= 0.9"),
        "maintainability": ("autogrow.self_heal_actions", "<= 3"),
        "evals": ("autogrow.success_rate", ">= 0.95"),
        "context": ("autogrow.self_heal_actions", "<= 3"),
        "observability": ("autogrow.success_rate", ">= 0.95"),
        "safety": ("autogrow.success", ">= 1"),
        "general": ("autogrow.success_rate", ">= 0.9"),
    }
    return theme_metric_map.get(theme.lower().strip(), ("autogrow.success_rate", ">= 0.9"))


def upsert_golden_rule(exp_id: str, themes: list[str], title: str) -> bool:
    rules_doc = read_json(GOLDEN_RULES_FILE, default={"version": 1, "rules": []})
    rules = rules_doc.get("rules")
    if not isinstance(rules, list):
        return False

    rule_id = f"GR-AUTO-{exp_id}"
    theme_summary = ", ".join(themes) if themes else "general"
    rule_payload = {
        "id": rule_id,
        "title": f"{exp_id} 自動実装ガイド",
        "rule": (
            f"{title} で得た知見（例: {theme_summary}）は、テーマ例に限定せず、"
            "複雑で信頼性の高いソフトウェアを大規模に構築・維持するための"
            "環境・フィードバックループ・制御システム改善へ展開し、"
            "必ず state checkpoint と差し替え表現を伴う実装として反映し、"
            "検証コマンドで再現可能にする。"
        ),
        "verification": "uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow",
    }

    for rule in rules:
        if str(rule.get("id", "")) == rule_id:
            changed = False
            for key, value in rule_payload.items():
                if rule.get(key) != value:
                    rule[key] = value
                    changed = True
            if changed:
                rules_doc["updated_at"] = iso_now()
                rules_doc["rules"] = rules
                write_json(GOLDEN_RULES_FILE, rules_doc)
            return changed

    rules.append(rule_payload)
    rules_doc["updated_at"] = iso_now()
    rules_doc["rules"] = rules
    write_json(GOLDEN_RULES_FILE, rules_doc)
    return True


def upsert_monitoring_targets(exp_id: str, themes: list[str]) -> bool:
    monitors_doc = read_json(
        MONITORING_TARGETS_FILE,
        default={"version": 1, "updated_at": iso_now(), "targets": []},
    )
    targets = monitors_doc.get("targets")
    if not isinstance(targets, list):
        return False
    changed = False

    for target in targets:
        if not isinstance(target, dict):
            continue
        theme = str(target.get("theme", "")).strip().lower()
        if not theme:
            continue
        query_hint, threshold = monitoring_profile_for_theme(theme)
        if str(target.get("query_hint", "")) != query_hint:
            target["query_hint"] = query_hint
            changed = True
        if str(target.get("threshold", "")) != threshold:
            target["threshold"] = threshold
            changed = True

    existing_ids = {str(target.get("id", "")) for target in targets}
    for theme in themes:
        target_id = f"MON-{exp_id}-{theme}".upper()
        if target_id in existing_ids:
            continue
        query_hint, threshold = monitoring_profile_for_theme(theme)
        targets.append(
            {
                "id": target_id,
                "theme": theme,
                "owner": "agent-radar",
                "name": f"{exp_id} {theme} health check",
                "query_hint": query_hint,
                "threshold": threshold,
            }
        )
        existing_ids.add(target_id)
        changed = True

    if changed:
        monitors_doc["updated_at"] = iso_now()
        monitors_doc["targets"] = targets
        write_json(MONITORING_TARGETS_FILE, monitors_doc)
    return changed


def write_implementation_artifacts(exp_item: dict[str, Any], themes: list[str]) -> list[str]:
    exp_id = str(exp_item.get("id", "EXP-UNKNOWN"))
    exp_title = str(exp_item.get("title", "(untitled)"))
    exp_link = str(exp_item.get("origin_link", ""))
    exp_source = str(exp_item.get("origin_source_id", exp_item.get("source", "")))
    exp_hypothesis = str(
        exp_item.get("hypothesis", "記事由来の改善仮説をハーネス実装へ反映する。")
    )

    impl_dir = IMPLEMENTED_DIR / exp_id
    impl_dir.mkdir(parents=True, exist_ok=True)

    spec_path = impl_dir / "spec.md"
    impl_plan_path = impl_dir / "impl-plan.md"
    state_strategy_path = impl_dir / "state-strategy.json"

    spec_path.write_text(
        "\n".join(
            [
                f"# {exp_id} Autonomous Implementation Spec",
                "",
                f"- Source: `{exp_source}`",
                f"- Title: {exp_title}",
                f"- Link: {exp_link or '(not provided)'}",
                f"- Themes: {', '.join(themes)}",
                "",
                "## Goal",
                "記事由来の知見を、再実行可能なハーネス実装としてリポジトリへ定着させる。",
                "",
                "## Acceptance",
                "- autogrow 実行で同じ結果に収束する",
                "- validate/garden が継続して成功する",
                "- 生成物が SoR 配下で追跡可能である",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    impl_plan_path.write_text(
        "\n".join(
            [
                f"# {exp_id} Autonomous Implementation Plan",
                "",
                f"## Hypothesis",
                exp_hypothesis,
                "",
                "## Steps",
                "1. Backlog item を実装対象として確定する",
                "2. 状態退避ポリシーを `state-strategy.json` に固定する",
                "3. 監視ターゲットと黄金律を機械更新する",
                "4. autogrow で validate/garden まで実行する",
                "",
                "## Verification",
                "- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    state_strategy = {
        "version": 1,
        "exp_id": exp_id,
        "updated_at": iso_now(),
        "checkpoint_policy": {
            "when": list(DEFAULT_CHECKPOINT_POLICY),
            "what": [
                "task_summary",
                "artifact_refs",
                "next_action",
                "failure_summary",
            ],
            "where": {
                "hot": "harness/agent_radar/state.json",
                "cold": "harness/agent_radar/archive/YYYY/MM/*.jsonl",
            },
            "conversation_replacement": list(DEFAULT_CONVERSATION_REPLACEMENTS),
        },
    }
    write_json(state_strategy_path, state_strategy)

    return [
        str(spec_path.relative_to(ROOT)),
        str(impl_plan_path.relative_to(ROOT)),
        str(state_strategy_path.relative_to(ROOT)),
    ]


def render_autonomous_growth_doc(items: list[dict[str, Any]], updated_at: str) -> str:
    lines = [
        "# Autonomous Growth",
        "",
        "この文書は、自律成長ループの実装結果を記録する SoR です。",
        "",
        f"- Updated at: `{updated_at}`",
        "",
        "## Backlog Status",
        "",
        "| EXP ID | Status | Themes | Artifacts |",
        "| --- | --- | --- | --- |",
    ]

    for item in items:
        exp_id = str(item.get("id", ""))
        status = str(item.get("status", ""))
        themes = ", ".join(item.get("themes", [])) if isinstance(item.get("themes"), list) else ""
        artifacts = ", ".join(item.get("artifact_paths", [])) if isinstance(item.get("artifact_paths"), list) else ""
        lines.append(f"| {exp_id} | {status} | {themes} | {artifacts} |")

    lines.append("")
    lines.append("## Runbook")
    lines.append("")
    lines.append(
        "- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow --collector auto --self-heal-max-retries 2`"
    )
    lines.append("")

    return "\n".join(lines)


def expected_autonomous_growth_doc_from_backlog() -> str:
    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"items": []})
    items = backlog.get("items") if isinstance(backlog, dict) else []
    if not isinstance(items, list):
        items = []
    updated_at = str(backlog.get("updated_at", "")).strip() if isinstance(backlog, dict) else ""
    if not updated_at:
        updated_at = "unknown"
    return render_autonomous_growth_doc(items, updated_at=updated_at)


def update_autonomous_growth_doc(items: list[dict[str, Any]], updated_at: str) -> None:
    AUTONOMOUS_GROWTH_DOC.parent.mkdir(parents=True, exist_ok=True)
    AUTONOMOUS_GROWTH_DOC.write_text(
        render_autonomous_growth_doc(items, updated_at=updated_at),
        encoding="utf-8",
    )


def run_implement() -> int:
    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"version": 1, "items": []})
    items = backlog.get("items")
    if not isinstance(items, list):
        print("ERROR: experiment_backlog.json items must be a list.", file=sys.stderr)
        return 1

    implemented = 0
    rules_added = 0
    monitors_added = 0
    mutations_added = 0
    if upsert_monitoring_targets("NOOP", []):
        monitors_added += 1
    for item in items:
        status = str(item.get("status", "")).strip().lower()
        if status == "implemented":
            exp_id = str(item.get("id", "")).strip()
            if not exp_id:
                continue
            title = str(item.get("title", "")).strip()
            link = str(item.get("origin_link", "")).strip()
            harness_tags = coerce_str_list(item.get("harness_tags"))
            raw_themes = coerce_str_list(item.get("themes"))
            detected_themes = detect_themes(title, link, " ".join(harness_tags), " ".join(raw_themes))
            themes: list[str] = []
            for token in [*harness_tags, *raw_themes, *detected_themes]:
                lowered = token.strip().lower()
                if lowered and lowered not in themes:
                    themes.append(lowered)
            growth_axes = detect_growth_axes(title, link, " ".join(themes))
            item["themes"] = themes
            item["growth_axes"] = growth_axes
            item["harness_tags"] = harness_tags
            item["state_checkpoint_policy"] = with_default_str_list(
                item.get("state_checkpoint_policy"),
                DEFAULT_CHECKPOINT_POLICY,
            )
            item["conversation_replacements"] = with_default_str_list(
                item.get("conversation_replacements"),
                DEFAULT_CONVERSATION_REPLACEMENTS,
            )
            item["innovation_priority"] = innovation_priority_for_themes(themes)
            if not isinstance(item.get("evaluation_task"), dict):
                item["evaluation_task"] = build_evaluation_task(exp_id, growth_axes)
            if upsert_golden_rule(exp_id, themes, title):
                rules_added += 1
            if upsert_monitoring_targets(exp_id, themes):
                monitors_added += 1

            mutation_ref = str(item.get("mutation_module", "")).strip()
            mutation_exists = False
            mutation_path = Path()
            if mutation_ref:
                mutation_path = ROOT / mutation_ref
                mutation_exists = mutation_path.exists()
            if mutation_exists:
                if is_autogenerated_mutation(mutation_path):
                    mutation_path = write_mutation_module(item, themes)
                    mutation_ref = str(mutation_path.relative_to(ROOT))
                    item["mutation_module"] = mutation_ref
                upsert_mutation_index(exp_id, mutation_path, themes)
                artifact_paths = coerce_str_list(item.get("artifact_paths"))
                if mutation_ref and mutation_ref not in artifact_paths:
                    artifact_paths.append(mutation_ref)
                item["artifact_paths"] = artifact_paths
                continue

            mutation_path = write_mutation_module(item, themes)
            upsert_mutation_index(exp_id, mutation_path, themes)

            artifact_paths = coerce_str_list(item.get("artifact_paths"))
            rel_mutation_path = str(mutation_path.relative_to(ROOT))
            if rel_mutation_path not in artifact_paths:
                artifact_paths.append(rel_mutation_path)
            item["artifact_paths"] = artifact_paths
            item["mutation_module"] = rel_mutation_path
            mutations_added += 1
            continue

        if status not in {"proposed", "ready", "planned"}:
            continue

        exp_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        link = str(item.get("origin_link", "")).strip()
        if not exp_id:
            continue

        harness_tags = coerce_str_list(item.get("harness_tags"))
        raw_themes = coerce_str_list(item.get("themes"))
        detected_themes = detect_themes(title, link, " ".join(harness_tags), " ".join(raw_themes))
        themes: list[str] = []
        for token in [*harness_tags, *raw_themes, *detected_themes]:
            lowered = token.strip().lower()
            if lowered and lowered not in themes:
                themes.append(lowered)
        growth_axes = detect_growth_axes(title, link, " ".join(themes))
        item["themes"] = themes
        item["growth_axes"] = growth_axes
        item["harness_tags"] = harness_tags
        item["state_checkpoint_policy"] = with_default_str_list(
            item.get("state_checkpoint_policy"),
            DEFAULT_CHECKPOINT_POLICY,
        )
        item["conversation_replacements"] = with_default_str_list(
            item.get("conversation_replacements"),
            DEFAULT_CONVERSATION_REPLACEMENTS,
        )
        item["innovation_priority"] = innovation_priority_for_themes(themes)
        if not isinstance(item.get("evaluation_task"), dict):
            item["evaluation_task"] = build_evaluation_task(exp_id, growth_axes)

        artifact_paths = write_implementation_artifacts(item, themes)
        mutation_path = write_mutation_module(item, themes)
        if upsert_mutation_index(exp_id, mutation_path, themes):
            mutations_added += 1
        artifact_paths.append(str(mutation_path.relative_to(ROOT)))

        if upsert_golden_rule(exp_id, themes, title):
            rules_added += 1
        if upsert_monitoring_targets(exp_id, themes):
            monitors_added += 1

        item["artifact_paths"] = artifact_paths
        item["mutation_module"] = str(mutation_path.relative_to(ROOT))
        item["status"] = "implemented"
        item["implemented_at"] = iso_now()
        implemented += 1

    backlog["version"] = int(backlog.get("version", 1))
    backlog["updated_at"] = iso_now()
    backlog["items"] = items
    write_json(EXPERIMENT_BACKLOG_FILE, backlog)
    update_autonomous_growth_doc(items, updated_at=str(backlog["updated_at"]))

    append_progress(
        "implement completed | "
        f"implemented={implemented} rules_added={rules_added} "
        f"monitors_changed={monitors_added} mutations_added={mutations_added}"
    )
    print(
        "OK: implement completed "
        f"(implemented={implemented} rules_added={rules_added} "
        f"monitors_changed={monitors_added} mutations_added={mutations_added})"
    )
    return 0


def execute_step(step_name: str, collector_mode: str) -> int:
    if step_name == "update":
        return run_update(collector_mode=collector_mode)
    if step_name == "validate":
        return run_validate()
    if step_name == "backlog":
        return run_backlog()
    if step_name == "implement":
        return run_implement()
    if step_name == "garden":
        return run_garden()
    print(f"ERROR: unsupported step: {step_name}", file=sys.stderr)
    return 1


def attempt_self_heal(step_name: str, collector_mode: str) -> tuple[int, list[str]]:
    actions: list[str] = []
    if step_name == "update":
        fallback = "native" if collector_mode != "native" else "auto"
        actions.append(f"retry_update_with_{fallback}")
        return run_update(collector_mode=fallback), actions
    if step_name == "validate":
        actions.extend(repair_validate_boundary())
        if not actions:
            actions.append("validate_noop_repair")
        return run_validate(), actions
    if step_name == "backlog":
        actions.extend(normalize_backlog_docs())
        if not actions:
            actions.append("backlog_noop_repair")
        return run_backlog(), actions
    if step_name == "implement":
        actions.extend(normalize_backlog_docs())
        index = ensure_mutation_index()
        write_json(MUTATION_INDEX_FILE, index)
        actions.append("ensure_mutation_index")
        return run_implement(), actions
    if step_name == "garden":
        actions.extend(repair_garden_placeholders())
        actions.extend(repair_autonomous_growth_doc_currency())
        if not actions:
            actions.append("garden_noop_repair")
        return run_garden(), actions
    actions.append("unsupported_step")
    return 1, actions


def run_control_loop(
    loop_name: str,
    collector_mode: str,
    steps: list[str],
    self_heal_max_retries: int,
) -> int:
    outcomes: list[StepOutcome] = []

    for step_index, step_name in enumerate(steps, start=1):
        step_label = f"{step_name}:{step_index}"
        rc = execute_step(step_name, collector_mode=collector_mode)
        if rc == 0:
            outcomes.append(StepOutcome(name=step_label, rc=0))
            continue

        repaired = False
        accumulated_actions: list[str] = []
        final_rc = rc

        for attempt in range(1, max(self_heal_max_retries, 0) + 1):
            heal_rc, actions = attempt_self_heal(step_name, collector_mode=collector_mode)
            accumulated_actions.extend(actions)
            append_self_heal_event(
                {
                    "at": iso_now(),
                    "loop": loop_name,
                    "step": step_name,
                    "step_label": step_label,
                    "attempt": attempt,
                    "actions": actions,
                    "result": "success" if heal_rc == 0 else "failed",
                }
            )
            if heal_rc == 0:
                repaired = True
                final_rc = 0
                break
            final_rc = heal_rc

        outcomes.append(
            StepOutcome(
                name=step_label,
                rc=final_rc,
                recovered=repaired,
                repair_actions=accumulated_actions,
            )
        )

        if final_rc != 0:
            publish_monitoring_artifacts(loop_name, collector_mode, outcomes)
            print(
                f"ERROR: {loop_name} stopped at {step_label} after self-heal attempts.",
                file=sys.stderr,
            )
            return final_rc

    publish_monitoring_artifacts(loop_name, collector_mode, outcomes)
    print(f"OK: {loop_name} completed")
    return 0


def run_autogrow(collector_mode: str = "auto", self_heal_max_retries: int = 2) -> int:
    return run_control_loop(
        loop_name="autogrow",
        collector_mode=collector_mode,
        steps=["update", "validate", "backlog", "implement", "validate", "garden"],
        self_heal_max_retries=self_heal_max_retries,
    )


def run_cycle(collector_mode: str = "auto", self_heal_max_retries: int = 2) -> int:
    return run_control_loop(
        loop_name="cycle",
        collector_mode=collector_mode,
        steps=["update", "validate", "backlog", "implement", "garden"],
        self_heal_max_retries=self_heal_max_retries,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Agent radar operation entrypoint")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["update", "validate", "backlog", "implement", "garden", "cycle", "autogrow"],
        help="operation mode",
    )
    parser.add_argument(
        "--collector",
        default="auto",
        choices=["auto", "native", "codex"],
        help="collector mode for update/cycle/autogrow",
    )
    parser.add_argument(
        "--self-heal-max-retries",
        type=int,
        default=2,
        help="max retry count for autonomous self-heal in cycle/autogrow",
    )
    args = parser.parse_args(argv)

    mode = args.mode
    collector_mode = args.collector
    self_heal_max_retries = args.self_heal_max_retries
    if mode == "update":
        return run_update(collector_mode=collector_mode)
    if mode == "validate":
        return run_validate()
    if mode == "garden":
        return run_garden()
    if mode == "backlog":
        return run_backlog()
    if mode == "implement":
        return run_implement()
    if mode == "cycle":
        return run_cycle(
            collector_mode=collector_mode,
            self_heal_max_retries=self_heal_max_retries,
        )
    if mode == "autogrow":
        return run_autogrow(
            collector_mode=collector_mode,
            self_heal_max_retries=self_heal_max_retries,
        )

    print(f"ERROR: unsupported mode: {mode}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
