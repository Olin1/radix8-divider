#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ROOT = Path(__file__).resolve().parents[1]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one EDA/DV stage, capture it, and rebuild the HTML dashboard.")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--title")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        parser.error("missing command after --")

    stage = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.stage)
    run_id = os.environ.get("REPORT_RUN_ID") or datetime.now().strftime("%Y%m%d-%H%M%S")
    report_root = Path(os.environ.get("REPORT_ROOT", ROOT / "reports"))
    run_dir = report_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    log_path = run_dir / f"{stage}.log"
    summary_path = run_dir / "summary.json"

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        summary = {
            "run_id": run_id,
            "started_at": now_iso(),
            "branch": git_value("branch", "--show-current"),
            "commit": git_value("rev-parse", "HEAD"),
            "commit_short": git_value("rev-parse", "--short", "HEAD"),
            "stages": {},
        }

    title = args.title or stage.replace("_", " ").title()
    started_at = now_iso()
    start = datetime.now()

    print(f"\n=== REPORT STAGE: {title} ===")
    print("Command:", " ".join(command))
    print("Report:", log_path.relative_to(ROOT) if log_path.is_relative_to(ROOT) else log_path)
    print()

    env = os.environ.copy()
    env["REPORT_RUN_ID"] = run_id
    rc = 127

    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"# Stage: {title}\n# Started: {started_at}\n# Command: {' '.join(command)}\n\n")
        try:
            proc = subprocess.Popen(
                command, cwd=ROOT, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace", bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                log.write(ANSI_RE.sub("", line))
            rc = proc.wait()
        except FileNotFoundError as exc:
            msg = f"ERROR: {exc}\n"
            sys.stdout.write(msg); log.write(msg); rc = 127
        except KeyboardInterrupt:
            sys.stdout.write("\nInterrupted.\n"); log.write("\nInterrupted.\n"); rc = 130

    duration = (datetime.now() - start).total_seconds()
    summary["ended_at"] = now_iso()
    summary["branch"] = git_value("branch", "--show-current")
    summary["commit"] = git_value("rev-parse", "HEAD")
    summary["commit_short"] = git_value("rev-parse", "--short", "HEAD")
    summary.setdefault("stages", {})[stage] = {
        "stage": stage,
        "title": title,
        "command": command,
        "started_at": started_at,
        "ended_at": now_iso(),
        "duration_seconds": round(duration, 3),
        "returncode": rc,
        "status": "PASS" if rc == 0 else "FAIL",
        "log": log_path.name,
    }
    atomic_json(summary_path, summary)

    builder = ROOT / "scripts" / "build_report_site.py"
    if builder.exists():
        subprocess.run([sys.executable, str(builder)], cwd=ROOT, check=False)

    if os.environ.get("AUTO_EXPORT_REPORTS", "1") not in ("0", "false", "False"):
        exporter = ROOT / "scripts" / "export_artifacts.py"
        if exporter.exists():
            subprocess.run([sys.executable, str(exporter), "--reports"], cwd=ROOT, check=False)
            if stage == "asic" and rc == 0:
                subprocess.run([sys.executable, str(exporter), "--layout"], cwd=ROOT, check=False)

    print(f"\n=== {title}: {'PASS' if rc == 0 else 'FAIL'} ({duration:.2f}s) ===")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
