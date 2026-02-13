#!/usr/bin/env python3
"""Agent radar control loop for in-repo System of Record."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
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
IMPLEMENTED_DIR = AGENT_RADAR_DIR / "implemented"
AUTONOMOUS_GROWTH_DOC = ROOT / "docs" / "agent-harness" / "autonomous-growth.md"
PROGRESS_LOG = ROOT / "harness" / "AI-Agent-progress.txt"
REPORTS_DIR = ROOT / "docs" / "reports" / "source-radar"
CODEX_AUDIT_DIR = REPORTS_DIR / "codex-exec"

GARDEN_TARGETS = [
    ROOT / "architecture" / "system-architecture.md",
    ROOT / "architecture" / "service-boundaries.md",
    ROOT / "architecture" / "deployment-topology.md",
    ROOT / "docs" / "agent-harness",
    ROOT / "plans" / "system" / "EPIC-SYS-002-harness-radar",
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
    "evals": ["eval", "benchmark", "swe-bench", "verification"],
    "context": ["context", "memory", "retrieval", "state", "checkpoint", "compaction"],
    "observability": ["trace", "metric", "log", "observability", "promql", "logql"],
    "safety": ["safety", "sandbox", "security", "guard"],
}


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


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def normalize_space(text: str) -> str:
    return " ".join(text.split())


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
            "- 推測禁止。不明項目は null を返すこと",
            "- 各ブログについて latest_title / latest_url / latest_date / method / evidence_url を1件返すこと",
            "- method は rss / atom / html のいずれか",
            "- possibleなら RSS/Atom を優先。なければ HTML 推定",
            "- latest_url と evidence_url は必ず許可されたブログ配下のURLのみ",
            "- 出力は JSON のみ。説明文や Markdown 禁止",
            "- 許可外URLを1件でも使った場合は {\"error\":\"OUT_OF_SCOPE\"} のみを返す",
            "",
            "【出力JSON】",
            "{",
            '  "checked_at": "<UTC ISO8601>",',
            '  "results": [',
            "    {",
            '      "site": "<homepage>",',
            '      "latest_title": "<string|null>",',
            '      "latest_url": "<string|null>",',
            '      "latest_date": "<string|null>",',
            '      "method": "<rss|atom|html>",',
            '      "evidence_url": "<string|null>"',
            "    }",
            "  ]",
            "}",
        ]
    )


def run_codex_exec(prompt: str, timeout_sec: int = 600) -> tuple[str, Path]:
    cmd = ["codex", "exec", prompt]
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as exc:
        stderr_text = (exc.stderr or "").strip()
        stdout_text = (exc.stdout or "").strip()
        audit_path = write_codex_audit(stdout_text, stderr_text, return_code=124)
        raise RuntimeError(f"codex exec timed out after {timeout_sec}s (audit={audit_path})") from exc

    audit_path = write_codex_audit(result.stdout, result.stderr, return_code=result.returncode)
    if result.returncode != 0:
        raise RuntimeError(f"codex exec failed with code={result.returncode} (audit={audit_path})")
    return result.stdout.strip(), audit_path


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

        if method not in {"rss", "atom", "html"}:
            raise RuntimeError(f"codex result has invalid method: {method} (audit={audit_path})")
        if not latest_title:
            raise RuntimeError(f"codex result latest_title is empty for site={homepage_key} (audit={audit_path})")
        if not latest_url:
            raise RuntimeError(f"codex result latest_url is empty for site={homepage_key} (audit={audit_path})")

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

    if collector_mode in {"auto", "codex"}:
        try:
            results, audit_path = collect_sources_with_codex_exec(sources)
            collector_used = "codex"
            append_progress(f"codex collector used | audit={audit_path.relative_to(ROOT)}")
        except RuntimeError as exc:
            if collector_mode == "codex":
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1
            collector_warnings.append(str(exc))

    if not results:
        results = [collect_source(source) for source in sources]
        collector_used = "native"

    for result in results:
        source_links = [item.link for item in result.items]
        current_set = set(source_links)
        previous_set = previous_links_map.get(result.source_id, set())

        for item in result.items:
            if item.link not in previous_set:
                new_items.append(
                    {
                        "source_id": result.source_id,
                        "title": item.title,
                        "link": item.link,
                        "published": item.published,
                        "collected_via": item.collected_via,
                        "evidence_url": item.evidence_url,
                    }
                )

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
        f"sources={len(snapshot_sources)} items={total_items} new={len(new_items)}"
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


def run_validate() -> int:
    cfg = read_json(OFFICIAL_SOURCES, default={})
    sources = cfg.get("sources", [])
    state = read_json(STATE_FILE, default={})
    snapshot = read_json(SNAPSHOT_FILE, default={})
    new_items_doc = read_json(NEW_ITEMS_FILE, default={})

    errors: list[str] = []
    errors.extend(validate_source_boundary(sources))

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

    if issues:
        for issue in issues:
            print(f"ERROR: unresolved placeholder: {issue}", file=sys.stderr)
        return 1

    print("OK: garden completed")
    return 0


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
        source_id = str(raw.get("source_id", "")).strip()
        title = normalize_space(str(raw.get("title", "")))
        link = str(raw.get("link", "")).strip()
        published = str(raw.get("published", "")).strip()

        if not source_id or not title or not link:
            continue
        if link in existing_links:
            continue

        exp_id = next_experiment_id(items)
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
                "acceptance": "Spec/Planへ反映し、評価結果と採否を記録する",
                "hypothesis": "記事の手法をハーネスへ適用し、品質ゲートまたは自律実行能力を改善できる",
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
    return matched


def upsert_golden_rule(exp_id: str, themes: list[str], title: str) -> bool:
    rules_doc = read_json(GOLDEN_RULES_FILE, default={"version": 1, "rules": []})
    rules = rules_doc.get("rules")
    if not isinstance(rules, list):
        return False

    rule_id = f"GR-AUTO-{exp_id}"
    for rule in rules:
        if str(rule.get("id", "")) == rule_id:
            return False

    theme_summary = ", ".join(themes)
    rules.append(
        {
            "id": rule_id,
            "title": f"{exp_id} 自動実装ガイド",
            "rule": (
                f"{title} で得た知見（{theme_summary}）は、"
                "必ず state checkpoint と差し替え表現を伴う実装として反映し、"
                "検証コマンドで再現可能にする。"
            ),
            "verification": "uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow",
        }
    )
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

    existing_ids = {str(target.get("id", "")) for target in targets}
    changed = False
    for theme in themes:
        target_id = f"MON-{exp_id}-{theme}".upper()
        if target_id in existing_ids:
            continue
        targets.append(
            {
                "id": target_id,
                "theme": theme,
                "owner": "agent-radar",
                "name": f"{exp_id} {theme} health check",
                "query_hint": "autogrow.success_rate",
                "threshold": ">= 0.95",
            }
        )
        existing_ids.add(target_id)
        changed = True

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
            "when": [
                "before_external_io",
                "before_long_running_loop",
                "before_quality_gate",
            ],
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
            "conversation_replacement": [
                "[[STATE_REF:<id>]]",
                "[[PLAN_REF:<epic>/<feature>]]",
                "[[EVAL_REF:<run>]]",
            ],
        },
    }
    write_json(state_strategy_path, state_strategy)

    return [
        str(spec_path.relative_to(ROOT)),
        str(impl_plan_path.relative_to(ROOT)),
        str(state_strategy_path.relative_to(ROOT)),
    ]


def update_autonomous_growth_doc(items: list[dict[str, Any]]) -> None:
    AUTONOMOUS_GROWTH_DOC.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Autonomous Growth",
        "",
        "この文書は、自律成長ループの実装結果を記録する SoR です。",
        "",
        f"- Updated at: `{iso_now()}`",
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
    lines.append("- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`")
    lines.append("")

    AUTONOMOUS_GROWTH_DOC.write_text("\n".join(lines), encoding="utf-8")


def run_implement() -> int:
    backlog = read_json(EXPERIMENT_BACKLOG_FILE, default={"version": 1, "items": []})
    items = backlog.get("items")
    if not isinstance(items, list):
        print("ERROR: experiment_backlog.json items must be a list.", file=sys.stderr)
        return 1

    implemented = 0
    rules_added = 0
    monitors_added = 0
    for item in items:
        status = str(item.get("status", "")).strip().lower()
        if status not in {"proposed", "ready", "planned"}:
            continue

        exp_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        link = str(item.get("origin_link", "")).strip()
        if not exp_id:
            continue

        themes = detect_themes(title, link)
        artifact_paths = write_implementation_artifacts(item, themes)

        if upsert_golden_rule(exp_id, themes, title):
            rules_added += 1
        if upsert_monitoring_targets(exp_id, themes):
            monitors_added += 1

        item["themes"] = themes
        item["artifact_paths"] = artifact_paths
        item["status"] = "implemented"
        item["implemented_at"] = iso_now()
        implemented += 1

    backlog["version"] = int(backlog.get("version", 1))
    backlog["updated_at"] = iso_now()
    backlog["items"] = items
    write_json(EXPERIMENT_BACKLOG_FILE, backlog)
    update_autonomous_growth_doc(items)

    append_progress(
        f"implement completed | implemented={implemented} rules_added={rules_added} monitors_changed={monitors_added}"
    )
    print(
        f"OK: implement completed (implemented={implemented} rules_added={rules_added} monitors_changed={monitors_added})"
    )
    return 0


def run_autogrow(collector_mode: str = "auto") -> int:
    rc = run_update(collector_mode=collector_mode)
    if rc != 0:
        return rc
    rc = run_validate()
    if rc != 0:
        return rc
    rc = run_backlog()
    if rc != 0:
        return rc
    rc = run_implement()
    if rc != 0:
        return rc
    rc = run_validate()
    if rc != 0:
        return rc
    rc = run_garden()
    if rc != 0:
        return rc
    print("OK: autogrow completed")
    return 0


def run_cycle(collector_mode: str = "auto") -> int:
    rc = run_update(collector_mode=collector_mode)
    if rc != 0:
        return rc
    rc = run_validate()
    if rc != 0:
        return rc
    rc = run_backlog()
    if rc != 0:
        return rc
    rc = run_implement()
    if rc != 0:
        return rc
    rc = run_garden()
    if rc != 0:
        return rc
    print("OK: cycle completed")
    return 0


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
    args = parser.parse_args(argv)

    mode = args.mode
    collector_mode = args.collector
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
        return run_cycle(collector_mode=collector_mode)
    if mode == "autogrow":
        return run_autogrow(collector_mode=collector_mode)

    print(f"ERROR: unsupported mode: {mode}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
