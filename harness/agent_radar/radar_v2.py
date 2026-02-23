#!/usr/bin/env python3
"""Harness V2: 自律的ハーネスエンジニアリング改良パイプライン。

V1（radar_ops.py）がブログのタイトル/URLだけを収集していたのに対し、
V2は記事本文を読み、ギャップ分析を行い、レビューループを経て、
実際のコードベース改修を実行する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import threading
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AGENT_RADAR_DIR = ROOT / "harness" / "agent_radar"
IDEAS_DIR = AGENT_RADAR_DIR / "ideas"
REJECTED_IDEAS_DIR = IDEAS_DIR / "rejected"
ANALYSIS_DIR = AGENT_RADAR_DIR / "analysis"
REVIEWS_DIR = AGENT_RADAR_DIR / "reviews"
EXECUTIONS_DIR = AGENT_RADAR_DIR / "executions"
KNOWLEDGE_BASE_FILE = AGENT_RADAR_DIR / "knowledge_base.json"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"
WORKTREE_RUNS_DIR = ROOT / "harness" / "worktree" / "runs"

from harness.agent_radar.radar_ops import (
    OFFICIAL_SOURCES,
    StepOutcome,
    append_progress,
    append_self_heal_event,
    iso_now,
    publish_monitoring_artifacts,
    read_json,
    repair_autonomous_growth_doc_currency,
    repair_garden_placeholders,
    repair_monitoring_artifact_freshness,
    run_garden,
    run_validate,
    write_json,
)

MAX_REVIEW_SESSIONS = 5
REVIEW_SCORE_MIN = 3
REVIEW_SCORE_AVG_MIN = 3.5

REVIEW_CRITERIA = [
    "harness_relevance",
    "feasibility",
    "risk",
    "roi",
    "sor_consistency",
]

SUPPLEMENTARY_SOURCES = [
    {"name": "Zenn", "search_prefix": "https://zenn.dev/search?q="},
    {"name": "Qiita", "search_prefix": "https://qiita.com/search?q="},
    {"name": "note", "search_prefix": "https://note.com/search?q="},
]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return iso_now()


def _read_json(path: Path, default: Any = None) -> Any:
    fallback = default if default is not None else {}
    return read_json(path, default=fallback)


def _write_json(path: Path, obj: Any) -> None:
    write_json(path, obj)


def _append_progress(summary: str) -> None:
    append_progress(f"harness-v2: {summary}")


def _emit(msg: str) -> None:
    print(f"INFO: {msg}", file=sys.stderr, flush=True)
    _append_progress(msg)


def _print_env_info() -> None:
    """Codex 実行前にユーザー・環境情報を表示する。"""
    import platform
    codex_exe = shutil.which("codex")
    home = str(Path.home())
    codex_home = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    local_config = CODEX_CONFIG
    python_version_file = ROOT / ".python-version"

    # Windows 11 は platform.release() が "10" と返るため、ビルド番号で判定
    # Windows 11 = ビルド 22000 以降
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
        "  Codex Execution Environment",
        "=" * 60,
        f"  Platform    : {os_display} ({platform.machine()})",
        f"  Python      : {python_display}",
        f"  Python exe  : {sys.executable}",
        f"  Codex CLI   : {codex_exe or 'NOT FOUND'}",
        f"  HOME        : {home}",
        f"  CODEX_HOME  : {codex_home}",
        f"  Project root: {ROOT}",
        f"  Config      : {local_config} (exists={local_config.exists()})",
    ]
    if local_config.exists():
        cfg = _read_codex_config()
        lines.append(f"  Model       : {cfg.get('model', '(default)')}")
        lines.append(f"  Sandbox     : {cfg.get('sandbox_mode', '(default)')}")
        lines.append(f"  Approval    : {cfg.get('approval_policy', '(default)')}")
    lines.append("=" * 60)
    for line in lines:
        print(line, file=sys.stderr, flush=True)


def _kill_headless_chrome() -> None:
    """前回残ったヘッドレス Chrome / chrome-devtools-mcp プロセスを終了する（Windows 専用）。"""
    if os.name != "nt":
        return
    try:
        _emit("killing stale headless Chrome / MCP processes...")
        wmic_cmd = [
            "wmic", "process", "where", "name='chrome.exe'",
            "get", "CommandLine,ProcessId", "/format:list",
        ]
        result = subprocess.run(
            wmic_cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            pids: list[str] = []
            current_cmd = ""
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("CommandLine="):
                    current_cmd = line[len("CommandLine="):]
                elif line.startswith("ProcessId="):
                    pid = line[len("ProcessId="):]
                    if "--headless" in current_cmd:
                        pids.append(pid)
                    current_cmd = ""
            if pids:
                _emit(f"headless Chrome PIDs: {', '.join(pids)}")
                for pid in pids:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

        wmic_all = [
            "wmic", "process", "get", "CommandLine,ProcessId", "/format:list",
        ]
        result_mcp = subprocess.run(
            wmic_all, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if result_mcp.returncode == 0:
            mcp_pids: list[str] = []
            current_cmd = ""
            for line in result_mcp.stdout.splitlines():
                line = line.strip()
                if line.startswith("CommandLine="):
                    current_cmd = line[len("CommandLine="):]
                elif line.startswith("ProcessId="):
                    pid = line[len("ProcessId="):]
                    if "chrome-devtools-mcp" in current_cmd:
                        mcp_pids.append(pid)
                    current_cmd = ""
            if mcp_pids:
                _emit(f"MCP PIDs: {', '.join(mcp_pids)}")
                for pid in mcp_pids:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

        _emit("headless Chrome cleanup done")
    except Exception as exc:
        _emit(f"headless Chrome cleanup failed (continuing): {exc}")


def _read_codex_config() -> dict[str, str]:
    if not CODEX_CONFIG.exists():
        return {}
    kv: dict[str, str] = {}
    for line in CODEX_CONFIG.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        kv[key] = value
    return kv


_codex_env_shown = False


def _run_codex_exec(prompt: str, timeout_sec: int = 600) -> str:
    """Codex CLI を実行し、stdoutを返す。"""
    global _codex_env_shown
    if not _codex_env_shown:
        _print_env_info()
        _kill_headless_chrome()
        time.sleep(1)
        _codex_env_shown = True

    cfg = _read_codex_config()
    codex_exe = (
        shutil.which("codex")
        or shutil.which("codex.cmd")
        or shutil.which("codex.exe")
    )
    if not codex_exe:
        raise RuntimeError(
            "codex command is not available in PATH. "
            "Install it (e.g. pip install codex-cli) and ensure it's in your PATH."
        )

    def _unquote(v: str) -> str:
        return v.strip().strip('"').strip("'")

    cmd: list[str] = [codex_exe, "exec"]
    model = cfg.get("model")
    if model:
        cmd += ["-m", _unquote(model)]
    sandbox = cfg.get("sandbox_mode")
    if sandbox:
        cmd += ["-s", _unquote(sandbox)]
    reasoning = cfg.get("model_reasoning_effort")
    if reasoning:
        cmd += ["-c", f"model_reasoning_effort={_unquote(reasoning)}"]
    approval = cfg.get("approval_policy")
    if approval:
        cmd += ["-c", f"approval_policy={_unquote(approval)}"]
    web_search = cfg.get("web_search")
    if web_search:
        cmd += ["-c", f"web_search={_unquote(web_search)}"]
    verbosity = cfg.get("text.verbosity") or cfg.get("verbosity")
    if verbosity:
        cmd += ["-c", f'text.verbosity="{_unquote(verbosity)}"']

    # プロンプトは stdin で渡し、クォート崩れを回避する
    _emit(f"codex exec started | timeout={timeout_sec}s prompt_len={len(prompt)}")
    _emit(f"codex command: {' '.join(cmd)}")

    env = os.environ.copy()
    user_home = str(Path.home())
    env.setdefault("USERPROFILE", user_home)
    env.setdefault("HOME", user_home)
    env["CODEX_HOME"] = str(Path.home() / ".codex")

    def _detect_encoding() -> str:
        if sys.platform != "win32":
            return "utf-8"
        try:
            test_proc = subprocess.run(
                [codex_exe, "--version"],
                capture_output=True,
                shell=codex_exe.lower().endswith((".cmd", ".bat")),
                timeout=5,
            )
            (test_proc.stdout or b"").decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "cp932"
        except Exception:
            return "utf-8"

    subprocess_encoding = _detect_encoding()
    _emit(f"codex encoding: {subprocess_encoding}")

    use_shell = codex_exe.lower().endswith((".cmd", ".bat"))
    popen_cmd: str | list[str] = subprocess.list2cmdline(cmd) if use_shell else cmd
    proc = subprocess.Popen(
        popen_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding=subprocess_encoding,
        errors="replace",
        env=env,
        cwd=str(ROOT),
        shell=use_shell,
    )

    start = time.monotonic()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    output_lock = threading.Lock()
    last_output_at = time.monotonic()

    def _reader(stream: Any, collector: list[str]) -> None:
        nonlocal last_output_at
        for line in iter(stream.readline, ""):
            value = line.rstrip("\n")
            collector.append(value)
            with output_lock:
                last_output_at = time.monotonic()

    assert proc.stdin is not None
    proc.stdin.write(prompt)
    proc.stdin.close()

    assert proc.stdout is not None and proc.stderr is not None
    t_out = threading.Thread(target=_reader, args=(proc.stdout, stdout_lines), daemon=True)
    t_err = threading.Thread(target=_reader, args=(proc.stderr, stderr_lines), daemon=True)
    t_out.start()
    t_err.start()

    idle_timeout_sec = 60
    timed_out = False
    idle_terminated = False
    while proc.poll() is None:
        now = time.monotonic()
        elapsed = now - start
        with output_lock:
            idle_for = now - last_output_at
        if elapsed > timeout_sec:
            timed_out = True
            proc.kill()
            break
        # 出力停止後のハングを緩和（stdout が一度でも出ていれば完了待ちで終了）
        if idle_for > idle_timeout_sec and stdout_lines:
            idle_terminated = True
            proc.terminate()
            time.sleep(2)
            if proc.poll() is None:
                proc.kill()
            break
        time.sleep(1)

    t_out.join(timeout=5)
    t_err.join(timeout=5)
    stdout = "\n".join(stdout_lines).strip()
    stderr = "\n".join(stderr_lines).strip()
    elapsed = int(time.monotonic() - start)

    if timed_out:
        raise RuntimeError(f"codex exec timed out after {timeout_sec}s")
    if idle_terminated:
        _emit(f"codex exec idle-terminated | elapsed={elapsed}s")

    if proc.returncode != 0 and not stdout:
        _emit(f"codex exec failed | code={proc.returncode} elapsed={elapsed}s")
        raise RuntimeError(f"codex exec failed: code={proc.returncode}\n{stderr[-1000:]}")

    if stderr:
        _emit(f"codex stderr captured | len={len(stderr)}")
    _emit(f"codex exec completed | elapsed={elapsed}s stdout_len={len(stdout)}")
    return stdout


def _extract_json(text: str) -> dict[str, Any]:
    """JSON を抽出。LLM が出力しがちな誤りを補正してからパースする。"""
    trimmed = text.strip()
    candidate = trimmed
    left = trimmed.find("{")
    right = trimmed.rfind("}")
    if left >= 0 and right > left:
        candidate = trimmed[left : right + 1]

    def try_parse(s: str) -> dict[str, Any] | None:
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    result = try_parse(candidate)
    if result is not None:
        return result

    # LLM が出力しがちな誤りを補正して再試行
    fixes = [
        (r',"\s*}', "}"),  # 最後の値の直後の ," を削除（","} -> }）
        (r',\s*}', "}"),   # オブジェクト末尾の trailing comma
        (r',\s*]', "]"),   # 配列末尾の trailing comma
    ]
    repaired = candidate
    for pattern, repl in fixes:
        repaired = re.sub(pattern, repl, repaired)
    result = try_parse(repaired)
    if result is not None:
        return result

    raise RuntimeError(f"Failed to extract JSON from output: {trimmed[:300]}")


def _next_id(prefix: str, directory: Path, pattern: str) -> str:
    max_no = 0
    if directory.exists():
        for path in directory.iterdir():
            m = re.match(pattern, path.stem)
            if m:
                no = int(m.group(1))
                if no > max_no:
                    max_no = no
    return f"{prefix}-{max_no + 1:03d}"


# ---------------------------------------------------------------------------
# Phase 1: Radar — 記事本文読み込み + アイデア抽出
# ---------------------------------------------------------------------------

def _build_blog_scrape_prompt(homepage_url: str, source_id: str, source_name: str) -> str:
    """chrome-devtools MCP でブログトップページを開き、最新記事の本文を取得するプロンプト。"""
    return (
        "【重要】このタスクは自動パイプラインです。挨拶・確認・質問は禁止。"
        "chrome-devtools.new_page を呼び、処理後に「JSONのみ」を出力すること。"
        "ツールが利用できない場合は、空の ideas を持つ最小JSONを出力すること。"
        "会話文で応答しないこと。\n\n"
        "## 手順（必ず実行）\n"
        f'1. tool `chrome-devtools.new_page({{"url": "{homepage_url}"}})` でブログトップページを開き、'
        "ページが安定するまで待つ。\n"
        "2. 表示されたページから最新の記事1件を特定する。\n"
        "3. その記事のリンクを開き、記事の本文を詳細に読み取る。\n"
        "4. 読み取った内容に基づき、以下のJSON形式で「のみ」出力する。説明文・Markdown・余計な文字は一切不要。\n"
        "\n"
        "## 背景\n"
        "- エージェントハーネス（Agent Harness）とは複雑で信頼性の高いソフトウェアを大規模に構築・維持する目標を達成するのに役立つ環境、フィードバックループ、これらが制御されたシステムのこと。噛み砕くとAIエージェント（特にLLM＝大規模言語モデル）を長時間・複雑なタスクで「ちゃんと動かせるようにする土台・インフラ」のこと。\n"
        "- ハーネスエンジニアリングは、メモリ管理、失敗からの復帰、自己修正、システムプロンプト、ツール選定、実行フローやミドルウェア（モデル呼び出し前後のフック）などを設計し、性能、トークン効率、レイテンシを最適化する考え方。\n"
        "- エージェントハーネスには、システムプロンプト、ツール、フック/ミドルウェア、スキル、サブエージェントの委譲、メモリシステムなど、多くのノブがあります。\n"
        "\n"
        f"## ソース情報\n"
        f"- ソースID: {source_id}\n"
        f"- ソース名: {source_name}\n"
        f"- ブログURL: {homepage_url}\n"
        "\n"
        "## 出力形式（JSON）\n"
        "{\n"
        '  "article_summary": "記事本文の詳細な日本語の要約（5-10文。技術的な内容を省略しないこと。）",\n'
        f'  "article_url": "記事の実際のURL",\n'
        f'  "article_title": "記事のタイトル",\n'
        f'  "source": "{source_name}",\n'
        f'  "source_id": "{source_id}",\n'
        '  "ideas": [\n'
        "    {\n"
        '      "title": "ハーネスエンジニアリングに適用可能なアイデアのタイトル",\n'
        '      "description": "アイデアの詳細説明（2-3文）",\n'
        '      "applicability_score": 4,\n'
        '      "harness_category": "environment|feedback_loop|control_system|reliability|observability|safety|scalability",\n'
        '      "rationale": "このアイデアがハーネス改善に役立つ理由"\n'
        "    }\n"
        "  ],\n"
        '  "supplementary_search_needed": true/false,\n'
        '  "supplementary_keywords": ["補足検索に使うキーワード"],\n'
        '  "chrome_devtools_used": true/false\n'
        "}\n"
        "\n"
        "## ハーネスエンジニアリングとの関連性判定基準（厳守）\n"
        "### ✅ 関連する内容（ideasを抽出）\n"
        "- AIエージェント、LLM、プロンプトエンジニアリング、RAGなどのソフトウェア技術\n"
        "- エラーハンドリング、リトライ、フォールバック、自己修復などの信頼性向上技術\n"
        "- トークン効率化、レイテンシ最適化、コスト削減などのパフォーマンス改善\n"
        "- ツールチェーン、API設計、メモリ管理、状態管理などのアーキテクチャ\n"
        "- テスト戦略、モニタリング、ロギング、可観測性などの品質保証\n"
        "- マルチエージェント協調、タスク分割、並列処理などのスケーラビリティ\n"
        "- システムプロンプト設計、Few-shot学習、Chain-of-Thought、推論戦略などLLM活用技術\n"
        "\n"
        "### ❌ 関連しない内容（ideas=[]で返す）\n"
        "- オフィス移転、物理的な施設・拠点、不動産関連の話題\n"
        "- 人事異動、組織再編、採用活動、社内イベントなど人・組織の話題\n"
        "- 企業の財務報告、株価、投資家向け情報\n"
        "- 製品発表、サービスリリース（AIエージェント技術に関する詳細が無い場合）\n"
        "- マーケティング、ブランディング、広報活動のみの内容\n"
        "- モデルのトレーニング、ファインチューニング、蒸留、データセット作成など「賢いモデルを作る」内容\n"
        "- モデルのトレーニングインフラ（分散学習基盤、RLフレームワーク、FP8学習、データパイプライン、GPU並列化戦略など）\n"
        "- モデルのアーキテクチャ設計（MoE、Attention改良、トークナイザ拡張、コンテキスト長拡張の内部実装など）\n"
        "- ベンチマークスコアの比較やモデル性能のランキングのみの内容\n"
        "  ★重要: ハーネスは訓練済みLLMをAPIやCLI経由で使う側の設計。モデル内部の訓練・推論基盤の改善はスコープ外。\n"
        "  「このトレーニング技術をハーネスの設計に応用できる」という類推的な関連付けは禁止。\n"
        "\n"
        "### 判定例\n"
        "❌ NG例: 「麻布台ヒルズへの移転で研究と実装のシナジー最大化」→ 物理的な場所の話でソフトウェア技術ではない\n"
        "❌ NG例: 「新しいファインチューニング手法で精度向上」→ モデルのトレーニングはスコープ外\n"
        "❌ NG例: 「非同期RLフレームワークで分散学習の安定性向上」→ モデルのトレーニングインフラでありスコープ外\n"
        "❌ NG例: 「FP8パイプラインでGPU並列化しスループット向上」→ モデル訓練/推論基盤の内部改善でありスコープ外\n"
        "❌ NG例: 「MoEアーキテクチャで活性化パラメータを削減」→ モデルアーキテクチャ設計でありスコープ外\n"
        "✅ OK例: 「LLMの推論時間を50%削減するプロンプトキャッシング手法」→ LLM利用側の性能最適化に直接適用可能\n"
        "✅ OK例: 「エージェントの失敗パターンを自動分類し再試行戦略を動的に選択する仕組み」→ 信頼性向上に直結\n"
        "✅ OK例: 「Few-shotプロンプトで複雑なタスクを段階的に分解する手法」→ LLM活用技術として有用\n"
        "✅ OK例: 「enable_thinkingフラグでCoT推論を制御しコスト/品質を動的に切替」→ API利用側のハーネス制御に有用\n"
        "❌ NG例: 「新CEOの就任と今後のビジョン」→ ソフトウェア技術の具体性がない\n"
        "\n"
        "## 注意事項\n"
        "- 記事本文をしっかり読んだ上で、上記の判定基準に厳密に従ってハーネスエンジニアリングに関連するアイデアを0〜5個抽出すること。\n"
        "- 関連するアイデアがない場合は必ず ideas を空配列にすること。曖昧な関連付けは禁止。\n"
        "- 推測禁止。実際に読んだ内容のみに基づくこと。出力は日本語にすること。\n"
        "- chrome_devtools_used: chrome-devtools.new_page を実際に使って取得した場合は true、ツールが利用できずフォールバックした場合は false。\n"
        "- chrome-devtools が使えない場合: "
        '{"article_url":"","article_title":"","article_summary":"","source":"' + source_name + '","source_id":"' + source_id + '","ideas":[],"supplementary_search_needed":false,"supplementary_keywords":[],"chrome_devtools_used":false} を出力。\n'
        "- 出力は必ずJSONオブジェクトのみ。前後に余計なテキストを付けないこと。"
    )


def _build_supplementary_search_prompt(keywords: list[str], original_article: str) -> str:
    """Zenn/Qiita/note を chrome-devtools で開いて補足記事を探すプロンプト。"""
    kw_str = ", ".join(keywords)
    search_urls = [
        f"https://zenn.dev/search?q={'+'.join(keywords)}",
        f"https://qiita.com/search?q={'+'.join(keywords)}",
    ]
    open_steps = "\n".join(
        f'{i+1}. tool `chrome-devtools.new_page({{"url": "{url}"}})` を開き、'
        "上位の記事タイトルと概要を確認する。"
        for i, url in enumerate(search_urls)
    )
    return (
        "【重要】自動パイプライン。挨拶・確認禁止。chrome-devtools.new_page で検索し、処理後にJSONのみ出力。"
        "ツール不可の場合は {\"supplementary_articles\":[],\"additional_ideas\":[],\"chrome_devtools_used\":false} を出力。会話文禁止。\n\n"
        f"## 元記事: {original_article}\n"
        f"## 検索キーワード: {kw_str}\n"
        "\n"
        "## 手順\n"
        f"{open_steps}\n"
        f"{len(search_urls)+1}. 関連性の高い記事があれば、そのリンクを開いて内容を読んでください。\n"
        f"{len(search_urls)+2}. 読んだ内容に基づいて以下のJSON形式で出力してください。\n"
        "\n"
        "## 出力形式（JSON）\n"
        "{\n"
        '  "supplementary_articles": [\n'
        "    {\n"
        '      "url": "記事URL",\n'
        '      "title": "記事タイトル",\n'
        '      "source": "zenn|qiita|note",\n'
        '      "key_insights": ["ハーネスに関連する洞察1", "洞察2"],\n'
        '      "relevance_score": 4\n'
        "    }\n"
        "  ],\n"
        '  "additional_ideas": [\n'
        "    {\n"
        '      "title": "追加のアイデアタイトル",\n'
        '      "description": "説明",\n'
        '      "applicability_score": 3,\n'
        '      "harness_category": "environment|feedback_loop|control_system|reliability|observability|safety",\n'
        '      "rationale": "理由",\n'
        f'      "derived_from": "{original_article}"\n'
        "    }\n"
        "  ],\n"
        '  "chrome_devtools_used": true\n'
        "}\n"
        "\n"
        "- chrome_devtools_used: chrome-devtools.new_page を実際に使った場合は true、ツール不可の場合は false。\n"
        "出力は必ずJSONオブジェクトのみ。説明文・前後のテキストは一切不要。"
    )


def run_radar() -> list[dict[str, Any]]:
    """6ブログの最新記事を chrome-devtools MCP で開き、本文を読んでアイデアを抽出する。

    official_sources.json の6ブログをループし、各ブログのトップページを
    Codex CLI 経由で chrome-devtools.new_page で開いて最新記事の詳細を取得する。
    """
    sources_cfg = read_json(OFFICIAL_SOURCES, default={"sources": []})
    sources = sources_cfg.get("sources", [])
    if not sources:
        _emit("radar skipped | no official sources configured")
        return []

    kb = _read_json(KNOWLEDGE_BASE_FILE, {"ideas": [], "rejected_ideas": [], "implemented_ideas": []})
    known_article_urls = {
        idea.get("source_url", "")
        for idea in [*kb.get("ideas", []), *kb.get("rejected_ideas", []), *kb.get("implemented_ideas", [])]
        if idea.get("source_url")
    }

    all_ideas: list[dict[str, Any]] = []

    for source in sources:
        source_id = source.get("id", "unknown")
        source_name = source.get("name", source_id)
        homepage = source.get("homepage", "")
        if not homepage:
            continue

        _emit(f"radar scraping blog | source={source_id} url={homepage}")

        try:
            prompt = _build_blog_scrape_prompt(homepage, source_id, source_name)
            result_text = _run_codex_exec(prompt, timeout_sec=600)
            result = _extract_json(result_text)
        except RuntimeError as exc:
            _emit(f"radar blog scrape failed | source={source_id} error={str(exc)[:200]}")
            continue

        article_url = result.get("article_url", "")
        article_title = result.get("article_title", "")
        article_summary = result.get("article_summary", "")

        if not article_url or not article_title:
            _emit(f"radar no article found | source={source_id}")
            continue

        if article_url in known_article_urls:
            _emit(f"radar article already known | source={source_id} url={article_url}")
            continue

        ideas = result.get("ideas", [])
        if not ideas:
            _emit(f"radar no harness ideas found | source={source_id} title={article_title[:60]}")
            continue

        chrome_used = result.get("chrome_devtools_used", False)
        for idea in ideas:
            idea["source_url"] = article_url
            idea["source_article_title"] = article_title
            idea["source_name"] = source_name
            idea["source_id"] = source_id
            idea["article_summary"] = article_summary
            idea["extracted_at"] = _utc_now_iso()
            idea["chrome_devtools_used"] = chrome_used

        # 補足情報源（Zenn/Qiita/note）からの追加情報収集
        if result.get("supplementary_search_needed") and result.get("supplementary_keywords"):
            _emit(f"radar supplementary search | keywords={result['supplementary_keywords']}")
            try:
                supp_prompt = _build_supplementary_search_prompt(
                    result["supplementary_keywords"], article_url
                )
                supp_text = _run_codex_exec(supp_prompt, timeout_sec=300)
                supp_result = _extract_json(supp_text)
                supp_chrome_used = supp_result.get("chrome_devtools_used", False)
                for extra_idea in supp_result.get("additional_ideas", []):
                    extra_idea["source_url"] = article_url
                    extra_idea["source_article_title"] = article_title
                    extra_idea["source_name"] = source_name
                    extra_idea["source_id"] = source_id
                    extra_idea["extracted_at"] = _utc_now_iso()
                    extra_idea["supplementary"] = True
                    extra_idea["chrome_devtools_used"] = supp_chrome_used
                    ideas.append(extra_idea)
            except RuntimeError as exc:
                _emit(f"radar supplementary search failed | error={str(exc)[:200]}")

        all_ideas.extend(ideas)
        known_article_urls.add(article_url)
        _emit(f"radar extracted {len(ideas)} ideas | source={source_id} chrome_devtools_used={chrome_used} title={article_title[:60]}")

    # アイデアを個別ファイルとして保存
    IDEAS_DIR.mkdir(parents=True, exist_ok=True)
    for idea in all_ideas:
        idea_id = _next_id("IDEA", IDEAS_DIR, r"IDEA-(\d+)")
        idea["id"] = idea_id
        _write_json(IDEAS_DIR / f"{idea_id}.json", idea)

    _emit(f"radar completed | sources_scanned={len(sources)} total_ideas={len(all_ideas)}")
    return all_ideas


# ---------------------------------------------------------------------------
# Phase 2: Analyze — ギャップ分析
# ---------------------------------------------------------------------------

def _build_gap_analysis_prompt(idea: dict[str, Any]) -> str:
    codebase_summary = _get_codebase_summary()
    return f"""あなたはハーネスエンジニアリングのアーキテクトです。

## タスク
以下のアイデアについて、現在のコードベースとのギャップ分析を行ってください。

## アイデア
- ID: {idea.get('id', 'N/A')}
- タイトル: {idea.get('title', '')}
- 説明: {idea.get('description', '')}
- カテゴリ: {idea.get('harness_category', '')}
- 適用可能性スコア: {idea.get('applicability_score', 'N/A')}

## 現在のコードベース概要
{codebase_summary}

## 分析要件
1. 現状分析: コードベースの該当領域の現在の状態
2. 理想状態: アイデアを適用した場合の理想
3. 差分: 現状→理想のギャップ
4. 効果分析: メリット・デメリット
5. 判定: adopt（採用）/ reject（不採用）/ investigate（要調査）

## 出力形式（JSON）
{{
  "idea_id": "{idea.get('id', '')}",
  "current_state": "現在の状態の説明",
  "ideal_state": "理想状態の説明",
  "gap_description": "ギャップの具体的な説明",
  "benefits": ["メリット1", "メリット2"],
  "risks": ["リスク1", "リスク2"],
  "effort_estimate": "small|medium|large",
  "verdict": "adopt|reject|investigate",
  "verdict_reason": "判定の理由",
  "implementation_sketch": "採用の場合、実装の概要",
  "affected_files": ["影響を受けるファイルのパス"],
  "directory_changes": {{
    "create": ["新規作成するディレクトリ"],
    "modify": ["変更するファイル"],
    "move": ["移動するファイル"]
  }}
}}

JSONのみ出力してください。"""


def _get_codebase_summary() -> str:
    """コードベースのハーネス関連部分の概要を生成する。"""
    summary_parts = []

    harness_dir = ROOT / "harness"
    if harness_dir.exists():
        files = []
        for p in harness_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                rel = p.relative_to(ROOT)
                size = p.stat().st_size
                files.append(f"  - {rel} ({size} bytes)")
        summary_parts.append("### harness/ ディレクトリ構造")
        summary_parts.extend(files[:50])

    docs_harness = ROOT / "docs" / "agent-harness"
    if docs_harness.exists():
        for p in docs_harness.iterdir():
            if p.is_file() and p.suffix == ".md":
                summary_parts.append(f"### {p.relative_to(ROOT)}")
                content = p.read_text(encoding="utf-8", errors="replace")
                summary_parts.append(content[:500])

    scripts_dir = ROOT / "scripts"
    if scripts_dir.exists():
        for p in scripts_dir.iterdir():
            if p.is_file():
                summary_parts.append(f"  - scripts/{p.name}")

    return "\n".join(summary_parts[:200])


def run_analyze(ideas: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """アイデアをコードベースと突き合わせてギャップ分析を行う。"""
    if ideas is None:
        ideas = []
        if IDEAS_DIR.exists():
            for p in sorted(IDEAS_DIR.glob("IDEA-*.json")):
                idea = _read_json(p, {})
                if idea.get("id") and not (ANALYSIS_DIR / f"GAP-{idea['id']}.json").exists():
                    ideas.append(idea)

    if not ideas:
        _emit("analyze skipped | no new ideas to analyze")
        return []

    kb = _read_json(KNOWLEDGE_BASE_FILE, {"ideas": [], "rejected_ideas": [], "implemented_ideas": []})
    analyses: list[dict[str, Any]] = []

    for idea in ideas:
        _emit(f"analyze gap analysis | idea={idea.get('id', 'N/A')} title={idea.get('title', '')[:50]}")

        try:
            prompt = _build_gap_analysis_prompt(idea)
            result_text = _run_codex_exec(prompt, timeout_sec=300)
            analysis = _extract_json(result_text)
        except RuntimeError as exc:
            _emit(f"analyze failed | idea={idea.get('id')} error={str(exc)[:200]}")
            continue

        analysis["analyzed_at"] = _utc_now_iso()
        gap_id = f"GAP-{idea.get('id', 'UNKNOWN')}"
        analysis["gap_id"] = gap_id

        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        _write_json(ANALYSIS_DIR / f"{gap_id}.json", analysis)

        verdict = analysis.get("verdict", "investigate")
        if verdict == "reject":
            rejected = {
                "id": idea.get("id", "").replace("IDEA", "IDEA-R"),
                "source_article": idea.get("source_article_title", ""),
                "source_url": idea.get("source_url", ""),
                "idea_summary": idea.get("description", ""),
                "rejected_at": _utc_now_iso(),
                "rejection_reason": analysis.get("verdict_reason", ""),
                "rejection_category": _classify_rejection(analysis),
                "scores": {"applicability": idea.get("applicability_score", 0)},
                "reconsider_trigger": analysis.get("reconsider_trigger", ""),
            }
            REJECTED_IDEAS_DIR.mkdir(parents=True, exist_ok=True)
            _write_json(REJECTED_IDEAS_DIR / f"{rejected['id']}.json", rejected)
            kb.setdefault("rejected_ideas", []).append(rejected)
            _emit(f"analyze rejected | idea={idea.get('id')} reason={analysis.get('verdict_reason', '')[:100]}")
        else:
            kb.setdefault("ideas", []).append({
                "id": idea.get("id", ""),
                "title": idea.get("title", ""),
                "source_url": idea.get("source_url", ""),
                "category": idea.get("harness_category", ""),
                "added_at": _utc_now_iso(),
            })

        analyses.append(analysis)

    kb["updated_at"] = _utc_now_iso()
    _write_json(KNOWLEDGE_BASE_FILE, kb)
    _emit(f"analyze completed | total={len(analyses)} adopted={sum(1 for a in analyses if a.get('verdict') == 'adopt')} rejected={sum(1 for a in analyses if a.get('verdict') == 'reject')}")
    return analyses


def _classify_rejection(analysis: dict[str, Any]) -> str:
    reason = (analysis.get("verdict_reason", "") + " " + " ".join(analysis.get("risks", []))).lower()
    if any(w in reason for w in ["infeasible", "不可能", "実装困難"]):
        return "infeasible"
    if any(w in reason for w in ["low roi", "効果が薄い", "投資対効果"]):
        return "low_roi"
    if any(w in reason for w in ["scope", "範囲外", "関係ない"]):
        return "out_of_scope"
    if any(w in reason for w in ["already", "既に", "実装済"]):
        return "already_implemented"
    if any(w in reason for w in ["risk", "危険", "リスク"]):
        return "too_risky"
    return "other"


# ---------------------------------------------------------------------------
# Phase 3: Backlog + Review Loop
# ---------------------------------------------------------------------------

def _build_plan_draft_prompt(analysis: dict[str, Any], idea: dict[str, Any]) -> str:
    return f"""あなたはハーネスエンジニアリングの実装計画を起草するエージェントです。

## 背景
以下のギャップ分析結果に基づき、具体的な実行計画を作成してください。

## アイデア
- タイトル: {idea.get('title', '')}
- 説明: {idea.get('description', '')}
- カテゴリ: {idea.get('harness_category', '')}

## ギャップ分析
- 現状: {analysis.get('current_state', '')}
- 理想: {analysis.get('ideal_state', '')}
- 差分: {analysis.get('gap_description', '')}
- 実装スケッチ: {analysis.get('implementation_sketch', '')}
- 影響ファイル: {json.dumps(analysis.get('affected_files', []), ensure_ascii=False)}

## 要件
- 実行計画はステップバイステップで記述
- 各ステップの成果物を明示
- ディレクトリ構造変更がある場合はマークダウンのリスト形式で記述
- ロールバック手順を含む
- 品質ゲート（validate/garden）の通過を最終確認に含む

## 出力形式（Markdown）
実行計画をMarkdown形式で出力してください。"""


def _build_review_prompt(plan_content: str, past_reviews: str, idea_title: str) -> str:
    return f"""あなたはハーネスエンジニアリングのレビュー担当エージェントです。

## レビュー対象
以下の実行計画をレビューしてください。

### 計画タイトル
{idea_title}

### 計画内容
{plan_content}

## 評価観点
以下の5軸で1-5のスコアを付けてください。
1. harness_relevance（ハーネス関連性）: ハーネスエンジニアリングの改良に直結するか
2. feasibility（実現可能性）: 現在のコードベースで実装可能か
3. risk（リスク）: 破壊的変更や副作用のリスクの低さ（5=低リスク）
4. roi（ROI）: 投入工数に対する改善効果
5. sor_consistency（SoR整合性）: 既存のSoR原則と矛盾しないか

## 過去のレビューメモ
{past_reviews if past_reviews else "（初回レビュー）"}

## 完了条件
- 全スコアが3以上 かつ 平均3.5以上で approve
- 改善不可能な問題がある場合は reject

## 出力形式（JSON）
{{
  "scores": {{
    "harness_relevance": 4,
    "feasibility": 4,
    "risk": 3,
    "roi": 4,
    "sor_consistency": 4
  }},
  "verdict": "approve|revise|reject",
  "comments": "具体的なレビューコメント",
  "focus_areas": ["修正が必要な箇所のリスト"],
  "strengths": ["計画の良い点"]
}}

JSONのみ出力してください。"""


def _build_fix_prompt(plan_content: str, review_result: dict[str, Any]) -> str:
    comments = review_result.get("comments", "")
    focus_areas = json.dumps(review_result.get("focus_areas", []), ensure_ascii=False)
    return f"""あなたはハーネスエンジニアリングの計画修正エージェントです。

## タスク
以下のレビュー指摘に基づいて、実行計画を修正してください。

## 現在の計画
{plan_content}

## レビュー指摘
- コメント: {comments}
- 要修正箇所: {focus_areas}
- スコア: {json.dumps(review_result.get('scores', {}), ensure_ascii=False)}

## 要件
- レビュー指摘を全て反映すること
- 計画の構造は維持しつつ、内容を改善すること
- 修正箇所には「[修正]」マーカーを入れること

## 出力
修正後の計画をMarkdown形式で出力してください。"""


def _check_review_passed(review: dict[str, Any]) -> bool:
    """レビュー完了条件のチェック。"""
    if review.get("verdict") != "approve":
        return False
    scores = review.get("scores", {})
    if not scores:
        return False
    values = [scores.get(c, 0) for c in REVIEW_CRITERIA]
    if any(v < REVIEW_SCORE_MIN for v in values):
        return False
    if sum(values) / len(values) < REVIEW_SCORE_AVG_MIN:
        return False
    return True


def run_review_loop(analysis: dict[str, Any], idea: dict[str, Any]) -> dict[str, Any]:
    """マルチセッションレビューループを実行する。

    各セッションは新しいCodex CLIプロセスで実行され、
    コンテキストがリセットされた状態でレビューが行われる。
    """
    idea_id = idea.get("id", "UNKNOWN")
    exp_id = analysis.get("idea_id", idea_id).replace("IDEA", "EXP")
    review_dir = REVIEWS_DIR / f"REV-{exp_id}"
    review_dir.mkdir(parents=True, exist_ok=True)

    _emit(f"review loop started | idea={idea_id} exp={exp_id}")

    plan_path = review_dir / "plan.md"
    status_path = review_dir / "status.json"

    status = {
        "exp_id": exp_id,
        "idea_id": idea_id,
        "status": "drafting",
        "sessions": [],
        "started_at": _utc_now_iso(),
    }

    # Step 1: 計画起草
    try:
        draft_prompt = _build_plan_draft_prompt(analysis, idea)
        plan_content = _run_codex_exec(draft_prompt, timeout_sec=300)
        plan_path.write_text(plan_content, encoding="utf-8")
        status["status"] = "reviewing"
        _write_json(status_path, status)
    except RuntimeError as exc:
        status["status"] = "draft_failed"
        status["error"] = str(exc)[:300]
        _write_json(status_path, status)
        _emit(f"review draft failed | idea={idea_id} error={str(exc)[:200]}")
        return status

    # Step 2: レビューループ
    past_reviews = ""
    for session_num in range(1, MAX_REVIEW_SESSIONS + 1):
        session_id = f"session-{session_num:03d}"
        session_file = review_dir / f"review-{session_id}.md"

        _emit(f"review session {session_num}/{MAX_REVIEW_SESSIONS} | idea={idea_id}")

        try:
            review_prompt = _build_review_prompt(
                plan_content, past_reviews, idea.get("title", "")
            )
            review_text = _run_codex_exec(review_prompt, timeout_sec=300)
            review_result = _extract_json(review_text)
        except RuntimeError as exc:
            session_record = {
                "session_id": session_id,
                "timestamp": _utc_now_iso(),
                "error": str(exc)[:300],
            }
            status["sessions"].append(session_record)
            _emit(f"review session failed | session={session_num} error={str(exc)[:200]}")
            continue

        session_record = {
            "session_id": session_id,
            "timestamp": _utc_now_iso(),
            "scores": review_result.get("scores", {}),
            "verdict": review_result.get("verdict", "unknown"),
            "comments": review_result.get("comments", ""),
            "focus_areas": review_result.get("focus_areas", []),
        }
        status["sessions"].append(session_record)

        review_md = f"""# Review Session {session_num}

- Session ID: {session_id}
- Timestamp: {session_record['timestamp']}
- Verdict: {review_result.get('verdict', 'unknown')}

## Scores
{json.dumps(review_result.get('scores', {}), ensure_ascii=False, indent=2)}

## Comments
{review_result.get('comments', '')}

## Focus Areas
{json.dumps(review_result.get('focus_areas', []), ensure_ascii=False, indent=2)}
"""
        session_file.write_text(review_md, encoding="utf-8")
        past_reviews += f"\n--- Session {session_num} ---\n{review_md}\n"

        if review_result.get("verdict") == "reject":
            status["status"] = "rejected"
            status["completed_at"] = _utc_now_iso()
            _write_json(status_path, status)
            _emit(f"review rejected | idea={idea_id} reason={review_result.get('comments', '')[:100]}")
            return status

        if _check_review_passed(review_result):
            status["status"] = "complete"
            status["completed_at"] = _utc_now_iso()
            _write_json(status_path, status)
            _emit(f"review approved | idea={idea_id} session={session_num}")
            return status

        # 修正が必要
        try:
            fix_prompt = _build_fix_prompt(plan_content, review_result)
            plan_content = _run_codex_exec(fix_prompt, timeout_sec=300)
            plan_path.write_text(plan_content, encoding="utf-8")
        except RuntimeError as exc:
            _emit(f"review fix failed | session={session_num} error={str(exc)[:200]}")

        _write_json(status_path, status)

    if status["status"] != "complete":
        status["status"] = "needs_human_review"
        status["completed_at"] = _utc_now_iso()
        _write_json(status_path, status)
        _emit(f"review max sessions reached | idea={idea_id}")

    return status


# ---------------------------------------------------------------------------
# Phase 4: Execute — 実際のコードベース改修
# ---------------------------------------------------------------------------

def _build_execution_prompt(plan_content: str, exp_id: str) -> str:
    return f"""あなたはハーネスエンジニアリングの実装エージェントです。

## タスク
以下の実行計画に基づいて、実際の変更を行うためのスクリプトを生成してください。

## 実行計画
{plan_content}

## 要件
1. 変更がディレクトリ構造に影響する場合:
   - まず、変更後のディレクトリ構造をマークダウンのリスト形式で出力
   - 次に、実際の変更を行うPythonスクリプトを生成
2. ファイルの新規作成・編集の場合:
   - 変更内容を具体的なPythonスクリプトとして出力
3. スクリプトはべき等であること（再実行しても安全）
4. エラーハンドリングを含むこと

## 出力形式（JSON）
{{
  "exp_id": "{exp_id}",
  "directory_structure": "変更後のディレクトリ構造（マークダウンリスト形式）",
  "changes": [
    {{
      "type": "create_file|edit_file|create_dir|move_file|delete_file",
      "path": "対象パス",
      "content": "ファイル内容（create_fileの場合）",
      "description": "変更の説明"
    }}
  ],
  "execution_script": "Pythonスクリプト本体（実行可能）",
  "rollback_script": "ロールバック用Pythonスクリプト",
  "commit_message": "包括的なコミットメッセージ（日本語）"
}}

JSONのみ出力してください。"""


def run_execute(review_status: dict[str, Any], plan_content: str) -> dict[str, Any]:
    """レビュー完了した計画に基づいて、隔離worktreeで改修を実行する。"""
    exp_id = review_status.get("exp_id", "UNKNOWN")
    exec_dir = EXECUTIONS_DIR / f"EXEC-{exp_id}"
    exec_dir.mkdir(parents=True, exist_ok=True)

    _emit(f"execute started | exp={exp_id}")

    try:
        prompt = _build_execution_prompt(plan_content, exp_id)
        result_text = _run_codex_exec(prompt, timeout_sec=600)
        execution = _extract_json(result_text)
    except RuntimeError as exc:
        result = {
            "exp_id": exp_id,
            "status": "generation_failed",
            "error": str(exc)[:300],
            "executed_at": _utc_now_iso(),
        }
        _write_json(exec_dir / "result.json", result)
        _emit(f"execute generation failed | exp={exp_id} error={str(exc)[:200]}")
        return result

    # ディレクトリ構造をSoR化
    dir_structure = execution.get("directory_structure", "")
    if dir_structure:
        (exec_dir / "dir-structure.md").write_text(
            f"# Directory Structure Change for {exp_id}\n\n{dir_structure}\n",
            encoding="utf-8",
        )

    # 変更スクリプトを保存
    exec_script = execution.get("execution_script", "")
    if exec_script:
        script_path = exec_dir / "change-script.py"
        script_path.write_text(exec_script, encoding="utf-8")

    # ロールバックスクリプトを保存
    rollback_script = execution.get("rollback_script", "")
    if rollback_script:
        (exec_dir / "rollback-script.py").write_text(rollback_script, encoding="utf-8")

    # worktree実行に使うFix Promptを保存（長文をCLI引数に乗せない）
    fix_prompt_path = exec_dir / "fix-prompt.txt"
    fix_prompt_path.write_text(
        "\n".join(
            [
                "以下の実行計画に従って、必要最小限の修正を実装してください。",
                "変更後は品質ゲート（validate/garden）が通る状態にしてください。",
                "",
                "## 実行計画",
                plan_content,
                "",
                "## 生成済み変更提案（参考）",
                json.dumps(execution.get("changes", []), ensure_ascii=False, indent=2),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_id = f"{exp_id}-{uuid.uuid4().hex[:8]}"
    worktree_cmd = [
        sys.executable,
        str(ROOT / "harness" / "worktree" / "worktree_ops.py"),
        "--task-id",
        task_id,
        "--base-ref",
        "HEAD",
        "--repro-cmd",
        "true",
        "--repro-expected-exit",
        "0",
        "--fix-prompt-file",
        str(fix_prompt_path),
        "--verify-cmd",
        "uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate && uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden",
        "--verify-expected-exit",
        "0",
        "--metrics-file",
        "harness/agent_radar/metrics/latest.json",
        "--keep-worktree",
    ]

    proc = subprocess.run(
        worktree_cmd,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (exec_dir / "worktree.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (exec_dir / "worktree.stderr.log").write_text(proc.stderr, encoding="utf-8")

    run_manifest_path = _resolve_latest_worktree_manifest(task_id)
    worktree_summary = ""
    if run_manifest_path is not None:
        run_manifest = _read_json(run_manifest_path, {})
        summary_rel = run_manifest.get("summary", "")
        if summary_rel:
            summary_path = ROOT / summary_rel
            if summary_path.exists():
                worktree_summary = str(summary_path.relative_to(ROOT))
    else:
        run_manifest = {}

    result = {
        "exp_id": exp_id,
        "status": "completed" if proc.returncode == 0 else "failed",
        "worktree_task_id": task_id,
        "worktree_manifest": str(run_manifest_path.relative_to(ROOT)) if run_manifest_path else "",
        "worktree_summary": worktree_summary,
        "errors": [] if proc.returncode == 0 else [f"worktree execution failed rc={proc.returncode}"],
        "commit_message": execution.get("commit_message", f"feat: {exp_id} ハーネス改善を適用"),
        "executed_at": _utc_now_iso(),
    }
    _write_json(exec_dir / "result.json", result)

    _emit(
        "execute completed | "
        f"exp={exp_id} status={result['status']} "
        f"task_id={task_id} manifest={result['worktree_manifest']}"
    )
    return result


def _resolve_latest_worktree_manifest(task_id: str) -> Path | None:
    if not WORKTREE_RUNS_DIR.exists():
        return None
    manifests = sorted(
        WORKTREE_RUNS_DIR.glob(f"*-{task_id}/run.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return manifests[0] if manifests else None


# ---------------------------------------------------------------------------
# Orchestrator: 全パイプラインの統合
# ---------------------------------------------------------------------------

def _publish_v2_metrics(
    ideas_count: int,
    analyses_count: int,
    adopted_count: int,
    rejected_count: int,
    reviews_approved: int,
    executions_completed: int,
    total_review_sessions: int,
) -> None:
    """V2パイプラインのメトリクスを metrics/latest.json に追記する。"""
    from harness.agent_radar.radar_ops import METRICS_LATEST_FILE
    latest = read_json(METRICS_LATEST_FILE, default={})
    if not isinstance(latest, dict):
        latest = {}
    metrics = latest.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    metrics["v2.ideas_extracted"] = float(ideas_count)
    metrics["v2.analyses_completed"] = float(analyses_count)
    metrics["v2.ideas_adopted"] = float(adopted_count)
    metrics["v2.ideas_rejected"] = float(rejected_count)
    metrics["v2.reviews_approved"] = float(reviews_approved)
    metrics["v2.executions_completed"] = float(executions_completed)
    avg_sessions = (total_review_sessions / reviews_approved) if reviews_approved > 0 else 0.0
    metrics["v2.avg_review_sessions"] = round(avg_sessions, 2)

    latest["metrics"] = metrics
    latest["v2_updated_at"] = _utc_now_iso()
    write_json(METRICS_LATEST_FILE, latest)
    _emit(f"v2 metrics published | ideas={ideas_count} adopted={adopted_count} executed={executions_completed}")


def _run_post_execute_gates() -> int:
    """V2実行後に validate と garden を実行する。"""
    _emit("phase 5: post-execute validate")
    rc = run_validate()
    if rc != 0:
        _emit(f"post-execute validate failed | rc={rc}")
        return rc

    _emit("phase 6: post-execute garden")
    rc = run_garden()
    if rc != 0:
        _emit(f"post-execute garden failed | rc={rc}")
        actions = repair_garden_placeholders()
        actions.extend(repair_autonomous_growth_doc_currency())
        _emit(f"post-execute garden self-heal | actions={actions}")
        rc = run_garden()

    return rc


def run_pipeline(collector_mode: str = "auto", self_heal_max_retries: int = 2) -> int:
    """V2パイプライン全体を実行する。

    1. Radar: 記事を読んでアイデア抽出
    2. Analyze: ギャップ分析
    3. Review Loop: 計画のレビュー
    4. Execute: 実際の改修
    5. Validate: V1のvalidateで改修後の整合性を検証
    6. Garden: V1のgardenで文書の劣化を修復
    """
    _emit(f"pipeline started | mode=v2 collector={collector_mode}")
    outcomes: list[StepOutcome] = []

    # Phase 1: Radar
    _emit("phase 1: radar (article analysis)")
    try:
        ideas = run_radar()
        outcomes.append(StepOutcome(name="radar:1", rc=0))
    except Exception as exc:
        _emit(f"pipeline failed | phase=radar error={str(exc)[:200]}")
        outcomes.append(StepOutcome(name="radar:1", rc=1))
        publish_monitoring_artifacts("pipeline", collector_mode, outcomes)
        return 1

    # Phase 2: Analyze
    _emit("phase 2: analyze (gap analysis)")
    analyses = run_analyze(ideas)
    outcomes.append(StepOutcome(name="analyze:2", rc=0))
    adopted = [a for a in analyses if a.get("verdict") == "adopt"]
    rejected_count = sum(1 for a in analyses if a.get("verdict") == "reject")

    # Phase 3+4: Review + Execute (for each adopted idea)
    executed = 0
    reviews_approved = 0
    total_review_sessions = 0

    for analysis in adopted:
        idea_id = analysis.get("idea_id", "")
        idea_file = IDEAS_DIR / f"{idea_id}.json"
        if not idea_file.exists():
            continue
        idea = _read_json(idea_file, {})

        # Phase 3: Review Loop
        _emit(f"phase 3: review loop | idea={idea_id}")
        review_status = run_review_loop(analysis, idea)
        total_review_sessions += len(review_status.get("sessions", []))

        if review_status.get("status") != "complete":
            _emit(f"pipeline skipped execution | idea={idea_id} review_status={review_status.get('status')}")
            continue

        reviews_approved += 1

        # Phase 4: Execute
        plan_path = REVIEWS_DIR / f"REV-{review_status.get('exp_id', '')}" / "plan.md"
        if not plan_path.exists():
            continue
        plan_content = plan_path.read_text(encoding="utf-8")

        _emit(f"phase 4: execute | idea={idea_id}")
        exec_result = run_execute(review_status, plan_content)

        if exec_result.get("status") == "completed":
            executed += 1
            outcomes.append(StepOutcome(name=f"execute:{idea_id}", rc=0))
        else:
            outcomes.append(
                StepOutcome(
                    name=f"execute:{idea_id}",
                    rc=1,
                    repair_actions=["worktree_execution_failed"],
                )
            )

    # Publish V2 metrics
    _publish_v2_metrics(
        ideas_count=len(ideas),
        analyses_count=len(analyses),
        adopted_count=len(adopted),
        rejected_count=rejected_count,
        reviews_approved=reviews_approved,
        executions_completed=executed,
        total_review_sessions=total_review_sessions,
    )

    # Phase 5+6: Post-execute validate + garden（常に実行）
    gate_rc = _run_post_execute_gates()
    if gate_rc == 0:
        outcomes.append(StepOutcome(name="validate_garden:post", rc=0))
    else:
        actions = repair_monitoring_artifact_freshness()
        retries = 0
        final_rc = gate_rc
        while retries < max(self_heal_max_retries, 0) and final_rc != 0:
            retries += 1
            append_self_heal_event(
                {
                    "at": _utc_now_iso(),
                    "loop": "pipeline",
                    "step": "validate_garden",
                    "step_label": "validate_garden:post",
                    "attempt": retries,
                    "actions": actions,
                    "result": "retrying",
                }
            )
            final_rc = _run_post_execute_gates()
        outcomes.append(
            StepOutcome(
                name="validate_garden:post",
                rc=final_rc,
                recovered=(final_rc == 0),
                repair_actions=actions,
            )
        )
        if final_rc != 0:
            _emit(f"pipeline post-execute gates failed | rc={final_rc}")

    publish_monitoring_artifacts("pipeline", collector_mode, outcomes)

    _emit(f"pipeline completed | ideas={len(ideas)} adopted={len(adopted)} executed={executed}")
    return 0 if all(outcome.rc == 0 for outcome in outcomes) else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Harness V2 autonomous improvement pipeline")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["radar", "analyze", "review", "execute", "pipeline"],
        help="operation mode",
    )
    parser.add_argument(
        "--collector",
        default="auto",
        choices=["auto", "codex"],
        help="collector mode for radar phase",
    )
    parser.add_argument(
        "--self-heal-max-retries",
        type=int,
        default=2,
        help="max retry count for post-execute gate self-heal",
    )
    args = parser.parse_args(argv)

    if args.mode == "radar":
        run_radar()
        return 0
    if args.mode == "analyze":
        run_analyze()
        return 0
    if args.mode == "pipeline":
        return run_pipeline(
            collector_mode=args.collector,
            self_heal_max_retries=args.self_heal_max_retries,
        )

    print(f"ERROR: mode '{args.mode}' not fully implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
