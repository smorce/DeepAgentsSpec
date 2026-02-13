#!/usr/bin/env python3
"""Isolated worktree task runner for reproduce -> fix -> evidence loop."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKTREE_ROOT = ROOT / "harness" / "worktree"
RUNS_DIR = WORKTREE_ROOT / "runs"
PROGRESS_LOG = ROOT / "harness" / "AI-Agent-progress.txt"


@dataclasses.dataclass
class PhaseResult:
    name: str
    command: str
    expected_exit: int
    actual_exit: int
    ok: bool
    started_at: str
    finished_at: str
    duration_sec: float
    stdout_path: str
    stderr_path: str


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]", "-", value.strip())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "task"


def append_progress(message: str) -> None:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("[%Y-%m-%d %H:%MZ]")
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} worktree-harness: {message}\n")


def run_shell_command(
    command: str,
    cwd: Path,
    timeout_sec: int,
    stdout_file: Path,
    stderr_file: Path,
) -> tuple[int, float]:
    started = time.monotonic()
    proc = subprocess.run(
        ["bash", "-lc", command],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        env=os.environ.copy(),
    )
    duration = time.monotonic() - started

    stdout_file.parent.mkdir(parents=True, exist_ok=True)
    stdout_file.write_text(proc.stdout, encoding="utf-8")
    stderr_file.parent.mkdir(parents=True, exist_ok=True)
    stderr_file.write_text(proc.stderr, encoding="utf-8")

    return proc.returncode, duration


def execute_phase(
    name: str,
    command: str,
    expected_exit: int,
    cwd: Path,
    timeout_sec: int,
    logs_dir: Path,
) -> PhaseResult:
    safe_name = slugify(name)
    stdout_file = logs_dir / f"{safe_name}.stdout.log"
    stderr_file = logs_dir / f"{safe_name}.stderr.log"
    started_at = iso_now()

    try:
        actual_exit, duration = run_shell_command(
            command=command,
            cwd=cwd,
            timeout_sec=timeout_sec,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )
    except subprocess.TimeoutExpired:
        timeout_message = (
            f"Command timed out after {timeout_sec}s while running phase '{name}'.\n"
            f"Command: {command}\n"
        )
        stderr_file.parent.mkdir(parents=True, exist_ok=True)
        stderr_file.write_text(timeout_message, encoding="utf-8")
        stdout_file.parent.mkdir(parents=True, exist_ok=True)
        stdout_file.write_text("", encoding="utf-8")
        actual_exit = 124
        duration = float(timeout_sec)

    finished_at = iso_now()
    return PhaseResult(
        name=name,
        command=command,
        expected_exit=expected_exit,
        actual_exit=actual_exit,
        ok=(actual_exit == expected_exit),
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round(duration, 3),
        stdout_path=str(stdout_file.relative_to(ROOT)),
        stderr_path=str(stderr_file.relative_to(ROOT)),
    )


def run_git_capture(worktree_dir: Path, artifacts_dir: Path) -> None:
    commands = {
        "git-status.txt": ["git", "-C", str(worktree_dir), "status", "--short"],
        "git-diff-stat.txt": ["git", "-C", str(worktree_dir), "diff", "--stat"],
        "git-diff.patch": ["git", "-C", str(worktree_dir), "diff"],
    }
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    for filename, cmd in commands.items():
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        output = result.stdout if result.returncode == 0 else result.stderr
        (artifacts_dir / filename).write_text(output, encoding="utf-8")


def capture_screenshot_if_requested(
    screenshot_url: str | None,
    output_path: Path,
    logs_dir: Path,
) -> dict[str, Any]:
    if not screenshot_url:
        return {"captured": False, "reason": "screenshot_url_not_provided"}

    if shutil.which("node") is None:
        return {"captured": False, "reason": "node_not_found"}

    node_script = """
const puppeteer = require('puppeteer');
(async () => {
  const url = process.argv[1];
  const output = process.argv[2];
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 });
  await page.screenshot({ path: output, fullPage: true });
  await browser.close();
})();
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "screenshot.stderr.log"
    result = subprocess.run(
        ["node", "-e", node_script, screenshot_url, str(output_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(result.stderr, encoding="utf-8")
        return {
            "captured": False,
            "reason": "screenshot_command_failed",
            "log_path": str(log_file.relative_to(ROOT)),
        }

    return {
        "captured": True,
        "path": str(output_path.relative_to(ROOT)),
    }


def copy_metric_sources(metric_files: list[str], worktree_dir: Path, metrics_dir: Path) -> list[str]:
    copied: list[str] = []
    if not metric_files:
        return copied

    target_dir = metrics_dir / "sources"
    target_dir.mkdir(parents=True, exist_ok=True)

    for index, raw_path in enumerate(metric_files, start=1):
        candidates = []
        candidate = Path(raw_path)
        if candidate.is_absolute():
            candidates.append(candidate)
        else:
            candidates.append((worktree_dir / candidate).resolve())
            candidates.append((ROOT / candidate).resolve())

        source = next((path for path in candidates if path.exists() and path.is_file()), None)
        if source is None:
            continue

        ext = source.suffix if source.suffix else ".txt"
        target = target_dir / f"{index:02d}-{slugify(source.stem)}{ext}"
        shutil.copy2(source, target)
        copied.append(str(target.relative_to(ROOT)))

    return copied


def build_replay_script(
    replay_path: Path,
    run_id: str,
    base_ref: str,
    setup_cmds: list[str],
    repro_cmd: str,
    fix_cmd: str | None,
    verify_cmd: str,
) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "REPO_ROOT=\"$(git rev-parse --show-toplevel)\"",
        f"RUN_ID={shlex.quote(run_id)}",
        f"BASE_REF={shlex.quote(base_ref)}",
        "REPLAY_DIR=\"$REPO_ROOT/harness/worktree/replay/$RUN_ID\"",
        "",
        "mkdir -p \"$(dirname \"$REPLAY_DIR\")\"",
        "git -C \"$REPO_ROOT\" worktree add --detach \"$REPLAY_DIR\" \"$BASE_REF\"",
        "cd \"$REPLAY_DIR\"",
        "",
    ]

    for command in setup_cmds:
        lines.append(f"bash -lc {shlex.quote(command)}")

    lines.append(f"bash -lc {shlex.quote(repro_cmd)}")
    if fix_cmd:
        lines.append(f"bash -lc {shlex.quote(fix_cmd)}")
    lines.append(f"bash -lc {shlex.quote(verify_cmd)}")
    lines.append("")

    replay_path.parent.mkdir(parents=True, exist_ok=True)
    replay_path.write_text("\n".join(lines), encoding="utf-8")
    replay_path.chmod(0o755)


def write_summary(
    summary_path: Path,
    run_id: str,
    task_id: str,
    base_ref: str,
    phases: list[PhaseResult],
    screenshot: dict[str, Any],
    metrics_copied: list[str],
    worktree_kept: bool,
    overall_ok: bool,
) -> None:
    lines = [
        "# Worktree Harness Run Summary",
        "",
        f"- run_id: `{run_id}`",
        f"- task_id: `{task_id}`",
        f"- base_ref: `{base_ref}`",
        f"- overall_status: `{'success' if overall_ok else 'failed'}`",
        f"- worktree_kept: `{str(worktree_kept).lower()}`",
        "",
        "## Phase Results",
        "",
        "| phase | expected_exit | actual_exit | ok | duration_sec | stdout | stderr |",
        "| --- | ---: | ---: | --- | ---: | --- | --- |",
    ]

    for phase in phases:
        lines.append(
            "| "
            f"{phase.name} | {phase.expected_exit} | {phase.actual_exit} | "
            f"{str(phase.ok).lower()} | {phase.duration_sec:.3f} | "
            f"`{phase.stdout_path}` | `{phase.stderr_path}` |"
        )

    lines.extend(["", "## Evidence"])
    if screenshot.get("captured") is True:
        lines.append(f"- screenshot: `{screenshot.get('path', '')}`")
    else:
        reason = screenshot.get("reason", "not_captured")
        lines.append(f"- screenshot: not captured (`{reason}`)")
        log_path = screenshot.get("log_path")
        if isinstance(log_path, str):
            lines.append(f"- screenshot_log: `{log_path}`")

    if metrics_copied:
        for metric_path in metrics_copied:
            lines.append(f"- metric_source: `{metric_path}`")
    else:
        lines.append("- metric_source: none")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run reproduce/fix/verify loop in an isolated git worktree and persist evidence."
    )
    parser.add_argument("--task-id", required=True, help="stable task identifier")
    parser.add_argument("--base-ref", default="HEAD", help="git ref to create the isolated worktree from")
    parser.add_argument("--setup-cmd", action="append", default=[], help="setup command run before reproduce")
    parser.add_argument("--repro-cmd", required=True, help="reproduction command")
    parser.add_argument(
        "--repro-expected-exit",
        type=int,
        default=1,
        help="expected exit code for reproduction command",
    )

    fix_group = parser.add_mutually_exclusive_group()
    fix_group.add_argument("--fix-cmd", help="fix command executed in worktree")
    fix_group.add_argument(
        "--fix-prompt",
        help="prompt for codex exec; converted to `codex exec <prompt>`",
    )

    parser.add_argument("--verify-cmd", required=True, help="verification command")
    parser.add_argument(
        "--verify-expected-exit",
        type=int,
        default=0,
        help="expected exit code for verify command",
    )
    parser.add_argument("--screenshot-url", help="URL to capture after verification")
    parser.add_argument(
        "--screenshot-path",
        default="screenshots/final.png",
        help="relative path under run directory for screenshot",
    )
    parser.add_argument(
        "--metrics-file",
        action="append",
        default=[],
        help="metric file path to copy into run artifacts",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=1800,
        help="timeout (sec) per phase command",
    )
    parser.add_argument(
        "--keep-worktree",
        action="store_true",
        help="keep generated worktree even when run succeeds",
    )
    parser.add_argument(
        "--cleanup-on-failure",
        action="store_true",
        help="force cleanup worktree when run fails",
    )

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if shutil.which("git") is None:
        print("ERROR: git command is required.", file=sys.stderr)
        return 1

    if not (ROOT / ".git").exists():
        print("ERROR: repository root is not a git checkout.", file=sys.stderr)
        return 1

    run_id = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(args.task_id)}"
    run_dir = RUNS_DIR / run_id
    worktree_dir = run_dir / "worktree"
    logs_dir = run_dir / "logs"
    artifacts_dir = run_dir / "artifacts"
    metrics_dir = run_dir / "metrics"
    evidence_dir = run_dir / "evidence"

    run_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    append_progress(f"start run_id={run_id} task={args.task_id} base_ref={args.base_ref}")

    add_cmd = ["git", "-C", str(ROOT), "worktree", "add", "--detach", str(worktree_dir), args.base_ref]
    add_result = subprocess.run(add_cmd, check=False, capture_output=True, text=True)
    if add_result.returncode != 0:
        (logs_dir / "worktree-add.stderr.log").write_text(add_result.stderr, encoding="utf-8")
        print(
            "ERROR: failed to create isolated worktree. See logs/worktree-add.stderr.log for details.",
            file=sys.stderr,
        )
        append_progress(f"failed run_id={run_id} reason=worktree_add_failed")
        return 1

    phases: list[PhaseResult] = []

    try:
        for index, setup_command in enumerate(args.setup_cmd, start=1):
            setup_phase = execute_phase(
                name=f"setup-{index}",
                command=setup_command,
                expected_exit=0,
                cwd=worktree_dir,
                timeout_sec=args.timeout_sec,
                logs_dir=logs_dir,
            )
            phases.append(setup_phase)
            if not setup_phase.ok:
                break

        setup_ok = all(phase.ok for phase in phases)
        if setup_ok:
            reproduce_phase = execute_phase(
                name="reproduce",
                command=args.repro_cmd,
                expected_exit=args.repro_expected_exit,
                cwd=worktree_dir,
                timeout_sec=args.timeout_sec,
                logs_dir=logs_dir,
            )
            phases.append(reproduce_phase)

            fix_command: str | None = None
            if args.fix_cmd:
                fix_command = args.fix_cmd
            elif args.fix_prompt:
                fix_command = f"codex exec {shlex.quote(args.fix_prompt)}"

            if fix_command is not None:
                fix_phase = execute_phase(
                    name="fix",
                    command=fix_command,
                    expected_exit=0,
                    cwd=worktree_dir,
                    timeout_sec=args.timeout_sec,
                    logs_dir=logs_dir,
                )
                phases.append(fix_phase)

            verify_phase = execute_phase(
                name="verify",
                command=args.verify_cmd,
                expected_exit=args.verify_expected_exit,
                cwd=worktree_dir,
                timeout_sec=args.timeout_sec,
                logs_dir=logs_dir,
            )
            phases.append(verify_phase)

        screenshot_result = capture_screenshot_if_requested(
            screenshot_url=args.screenshot_url,
            output_path=run_dir / args.screenshot_path,
            logs_dir=logs_dir,
        )

        metrics_copied = copy_metric_sources(
            metric_files=args.metrics_file,
            worktree_dir=worktree_dir,
            metrics_dir=metrics_dir,
        )

        run_git_capture(worktree_dir=worktree_dir, artifacts_dir=artifacts_dir)

        phase_json = [dataclasses.asdict(phase) for phase in phases]
        overall_ok = len(phases) > 0 and all(phase["ok"] for phase in phase_json)

        replay_fix_command: str | None = None
        if args.fix_cmd:
            replay_fix_command = args.fix_cmd
        elif args.fix_prompt:
            replay_fix_command = f"codex exec {shlex.quote(args.fix_prompt)}"

        replay_script = artifacts_dir / "replay.sh"
        build_replay_script(
            replay_path=replay_script,
            run_id=run_id,
            base_ref=args.base_ref,
            setup_cmds=args.setup_cmd,
            repro_cmd=args.repro_cmd,
            fix_cmd=replay_fix_command,
            verify_cmd=args.verify_cmd,
        )

        run_metrics = {
            "run_id": run_id,
            "task_id": args.task_id,
            "base_ref": args.base_ref,
            "generated_at": iso_now(),
            "overall_ok": overall_ok,
            "phase_count": len(phases),
            "phase_results": phase_json,
            "screenshot": screenshot_result,
            "metrics_sources": metrics_copied,
        }
        (metrics_dir / "run-metrics.json").write_text(
            json.dumps(run_metrics, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        summary_path = evidence_dir / "summary.md"
        worktree_kept = args.keep_worktree
        if not overall_ok and not args.cleanup_on_failure:
            worktree_kept = True

        write_summary(
            summary_path=summary_path,
            run_id=run_id,
            task_id=args.task_id,
            base_ref=args.base_ref,
            phases=phases,
            screenshot=screenshot_result,
            metrics_copied=metrics_copied,
            worktree_kept=worktree_kept,
            overall_ok=overall_ok,
        )

        run_manifest = {
            "run_id": run_id,
            "task_id": args.task_id,
            "base_ref": args.base_ref,
            "run_dir": str(run_dir.relative_to(ROOT)),
            "worktree_dir": str(worktree_dir.relative_to(ROOT)),
            "summary": str(summary_path.relative_to(ROOT)),
            "replay_script": str(replay_script.relative_to(ROOT)),
            "overall_ok": overall_ok,
            "generated_at": iso_now(),
        }
        (run_dir / "run.json").write_text(
            json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if worktree_kept:
            append_progress(f"complete run_id={run_id} status={'success' if overall_ok else 'failed'} kept=true")
            print(
                f"OK: run completed (status={'success' if overall_ok else 'failed'}) summary={summary_path.relative_to(ROOT)}"
            )
            return 0 if overall_ok else 1

        remove_result = subprocess.run(
            ["git", "-C", str(ROOT), "worktree", "remove", "--force", str(worktree_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if remove_result.returncode != 0:
            (logs_dir / "worktree-remove.stderr.log").write_text(remove_result.stderr, encoding="utf-8")
            append_progress(
                f"warning run_id={run_id} reason=worktree_remove_failed status={'success' if overall_ok else 'failed'}"
            )

        append_progress(
            f"complete run_id={run_id} status={'success' if overall_ok else 'failed'} kept=false"
        )
        print(
            f"OK: run completed (status={'success' if overall_ok else 'failed'}) summary={summary_path.relative_to(ROOT)}"
        )
        return 0 if overall_ok else 1

    finally:
        pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
