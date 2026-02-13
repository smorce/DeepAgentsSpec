#!/usr/bin/env python3
"""Agent radar control loop for in-repo System of Record."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
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
PROGRESS_LOG = ROOT / "harness" / "AI-Agent-progress.txt"
REPORTS_DIR = ROOT / "docs" / "reports" / "source-radar"

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


@dataclass
class RadarItem:
    title: str
    link: str
    published: str
    collected_via: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "link": self.link,
            "published": self.published,
            "collected_via": self.collected_via,
        }


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
        items.append(RadarItem(title=title, link=link, published=published, collected_via="rss"))
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
        items.append(RadarItem(title=title, link=link, published=published, collected_via="rss"))
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
        items.append(RadarItem(title=title, link=href, published="", collected_via="html"))
        if len(items) >= max_items:
            break

    return dedupe_items(items, max_items), []


def has_allowed_prefix(link: str, prefixes: list[str]) -> bool:
    return any(link.startswith(prefix) for prefix in prefixes)


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


def run_update() -> int:
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

    for source in sources:
        result = collect_source(source)
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
        "total_sources": len(snapshot_sources),
        "total_items": total_items,
        "sources": snapshot_sources,
    }
    state = {
        "version": 1,
        "last_run_at": now,
        "sources": state_sources,
    }
    new_items_doc = {
        "generated_at": now,
        "new_item_count": len(new_items),
        "new_items": new_items,
    }

    write_json(SNAPSHOT_FILE, snapshot)
    write_json(STATE_FILE, state)
    write_json(NEW_ITEMS_FILE, new_items_doc)
    write_daily_report(snapshot, new_items)

    append_progress(
        f"update completed | sources={len(snapshot_sources)} items={total_items} new={len(new_items)}"
    )

    print(
        f"OK: update completed (sources={len(snapshot_sources)} total_items={total_items} new_items={len(new_items)})"
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
        for item in source_snap.get("items", []):
            link = str(item.get("link", ""))
            if not has_allowed_prefix(link, allowed):
                errors.append(f"snapshot link out of boundary: {sid} {link}")

    for item in new_items_doc.get("new_items", []):
        sid = item.get("source_id", "")
        source_cfg = src_map.get(sid)
        link = str(item.get("link", ""))
        if not source_cfg:
            errors.append(f"new item has unknown source id: {sid}")
            continue
        allowed = source_cfg.get("allowed_entry_prefixes", [])
        if not has_allowed_prefix(link, allowed):
            errors.append(f"new item link out of boundary: {sid} {link}")

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


def run_cycle() -> int:
    rc = run_update()
    if rc != 0:
        return rc
    rc = run_validate()
    if rc != 0:
        return rc
    rc = run_backlog()
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
        choices=["update", "validate", "backlog", "garden", "cycle"],
        help="operation mode",
    )
    args = parser.parse_args(argv)

    mode = args.mode
    if mode == "update":
        return run_update()
    if mode == "validate":
        return run_validate()
    if mode == "garden":
        return run_garden()
    if mode == "backlog":
        return run_backlog()
    if mode == "cycle":
        return run_cycle()

    print(f"ERROR: unsupported mode: {mode}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
