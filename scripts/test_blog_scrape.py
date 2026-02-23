#!/usr/bin/env python3
"""V2 radar ブログスクレイプ部分の単体テスト用スクリプト。

codex exec + chrome-devtools MCP によるブログ記事取得を切り出して試す。
リポジトリルートから実行:

  uv run --no-project --link-mode=copy python scripts/test_blog_scrape.py [--source SOURCE_ID]

例:
  # 先頭ソース（qwen）で実行（デフォルト）
  uv run --no-project --link-mode=copy python scripts/test_blog_scrape.py

  # 特定ソースを指定
  uv run --no-project --link-mode=copy python scripts/test_blog_scrape.py --source deepseek

  # タイムアウトを 60 秒に変更
  uv run --no-project --link-mode=copy python scripts/test_blog_scrape.py --source sakana_ai --timeout 60

  # プロンプトだけ確認（codex は実行しない）
  uv run --no-project --link-mode=copy python scripts/test_blog_scrape.py --source qwen --prompt-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.agent_radar.radar_ops import read_json, OFFICIAL_SOURCES
from harness.agent_radar.radar_v2 import (
    _build_blog_scrape_prompt,
    _run_codex_exec,
    _extract_json,
)


def print_test_env_info(source_id: str, source_name: str, homepage: str, timeout: int, prompt_only: bool) -> None:
    """テスト実行前に環境情報を表示する。"""
    import platform
    import shutil
    
    ROOT = Path(__file__).resolve().parents[1]
    codex_exe = shutil.which("codex")
    home = str(Path.home())
    codex_home = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    local_config = ROOT / ".codex" / "config.toml"
    python_version_file = ROOT / ".python-version"

    # Windows 11 判定
    os_display = platform.system()
    if platform.system() == "Windows":
        try:
            build_num = int(platform.version().split(".")[-1])
            if build_num >= 22000:
                os_display = "Windows 11"
            else:
                os_display = f"Windows {platform.release()}"
        except Exception:
            os_display = f"Windows {platform.release()}"
    
    # Python バージョンは .python-version を優先
    python_display = sys.version.split()[0]
    if python_version_file.exists():
        try:
            py_ver_content = python_version_file.read_text(encoding="utf-8").strip()
            if py_ver_content:
                python_display = f"{py_ver_content} (from .python-version, actual: {sys.version.split()[0]})"
        except Exception:
            pass

    lines = [
        "=" * 60,
        "  Test Blog Scrape Environment",
        "=" * 60,
        f"  Platform    : {os_display} ({platform.machine()})",
        f"  Python      : {python_display}",
        f"  Python exe  : {sys.executable}",
        f"  Codex CLI   : {codex_exe or 'NOT FOUND'}",
        f"  HOME        : {home}",
        f"  CODEX_HOME  : {codex_home}",
        f"  Project root: {ROOT}",
        f"  Config      : {local_config} (exists={local_config.exists()})",
        "",
        f"  Target      : {source_id} ({source_name})",
        f"  Homepage    : {homepage}",
        f"  Timeout     : {timeout}s",
        f"  Prompt only : {prompt_only}",
        "=" * 60,
    ]
    for line in lines:
        print(line, file=sys.stderr, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="V2 ブログスクレイプ単体テスト")
    parser.add_argument(
        "--source",
        default=None,
        help="ソースID（未指定時は先頭）。例: qwen, deepseek, sakana_ai",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=500,
        help="codex exec タイムアウト秒 (default: 500)",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="プロンプトのみ出力し、codex は実行しない",
    )
    args = parser.parse_args()

    sources_cfg = read_json(OFFICIAL_SOURCES, default={"sources": []})
    sources = sources_cfg.get("sources", [])
    if not sources:
        print("ERROR: official_sources.json に sources がありません", file=sys.stderr)
        return 1

    if args.source:
        source = next((s for s in sources if s.get("id") == args.source), None)
        if not source:
            print(f"ERROR: ソース '{args.source}' が見つかりません", file=sys.stderr)
            print("利用可能:", ", ".join(s.get("id", "?") for s in sources), file=sys.stderr)
            return 1
    else:
        source = sources[0]

    source_id = source.get("id", "unknown")
    source_name = source.get("name", source_id)
    homepage = source.get("homepage", "")
    if not homepage:
        print("ERROR: homepage が空です", file=sys.stderr)
        return 1

    # 環境情報を表示
    print_test_env_info(source_id, source_name, homepage, args.timeout, args.prompt_only)
    print(file=sys.stderr)

    prompt = _build_blog_scrape_prompt(homepage, source_id, source_name)

    if args.prompt_only:
        print("--- プロンプト ---")
        print(prompt)
        print("--- 終了 ---")
        return 0

    print("codex exec 実行中...", file=sys.stderr, flush=True)
    try:
        result_text = _run_codex_exec(prompt, timeout_sec=args.timeout)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print()
    print("--- codex stdout (raw) ---")
    print(result_text)
    print("--- 終了 ---")

    try:
        result = _extract_json(result_text)
        print()
        print("--- パース済み JSON ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        ideas_count = len(result.get("ideas", []))
        print()
        print(f"OK | ideas={ideas_count} article_title={result.get('article_title', '')[:50]}...")
        return 0
    except RuntimeError as e:
        print()
        print(f"ERROR: JSON 抽出失敗: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
