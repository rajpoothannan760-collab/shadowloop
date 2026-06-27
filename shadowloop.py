#!/usr/bin/env python3
"""
shadowloop.py
─────────────
Monitors the current directory for file changes, runs a verification
command, and auto-commits when tests pass.

Usage:
    python shadowloop.py [--cmd "python -m unittest"]
"""

from __future__ import annotations

import argparse
import io
import shlex
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ── Configuration ────────────────────────────────────────────────────────────

EXCLUDED_DIRS: frozenset[str] = frozenset({".git", ".venv", "__pycache__"})
DEBOUNCE_SECONDS: float = 2.0
STDERR_TAIL_LINES: int = 50

# Resolve git at import time; fall back to known Windows install path
GIT_EXE: str = (
    shutil.which("git")
    or r"C:\Program Files\Git\cmd\git.exe"
)

# ── ANSI helpers ─────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
DIM    = "\033[2m"


def _panel(title: str, color: str, lines: list[str] | None = None) -> None:
    """Print a bordered status panel to stdout."""
    width = 60
    bar = "─" * width
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{color}{BOLD}┌{bar}┐{RESET}")
    print(f"{color}{BOLD}│  {title:<{width - 2}}│{RESET}")
    print(f"{color}{BOLD}│  {DIM}{timestamp:<{width - 2}}{RESET}{color}{BOLD}│{RESET}")
    print(f"{color}{BOLD}└{bar}┘{RESET}")
    if lines:
        print(f"{DIM}{'─' * width}{RESET}")
        for line in lines:
            print(f"  {line}")
        print(f"{DIM}{'─' * width}{RESET}")
    print()


# ── Core logic ───────────────────────────────────────────────────────────────

def _is_excluded(path: str) -> bool:
    """Return True if any component of *path* is an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in Path(path).parts)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def run_verification_loop(cmd: list[str]) -> None:
    """Execute the verification command and react to its result."""
    print(f"{CYAN}{BOLD}> {' '.join(cmd)}{RESET}  {DIM}(running...){RESET}")

    result = _run(cmd)

    if result.returncode != 0:
        # ── Failure path ─────────────────────────────────────────────────
        stderr_lines = (result.stderr or result.stdout or "").strip().splitlines()
        tail = stderr_lines[-STDERR_TAIL_LINES:]
        _panel("[REPAIR LOOP ACTIVE]  Tests failed — inspect errors below", RED, tail)

    else:
        # ── Success path ─────────────────────────────────────────────────
        _panel("[VALIDATION PASSED]  Auto-committing changes…", GREEN)

        add = _run([GIT_EXE, "add", "-A"])
        if add.returncode != 0:
            print(f"{RED}git add failed:{RESET}\n{add.stderr.strip()}")
            return

        commit = _run([GIT_EXE, "commit", "-m", "shadowloop: automatic test pass"])
        if commit.returncode == 0:
            print(f"{GREEN}{commit.stdout.strip()}{RESET}\n")
        else:
            # Gracefully handle "nothing to commit"
            msg = commit.stdout.strip() or commit.stderr.strip()
            print(f"{YELLOW}{msg}{RESET}\n")


# ── Watchdog handler ─────────────────────────────────────────────────────────

class _DebounceHandler(FileSystemEventHandler):
    """Debounced handler — waits DEBOUNCE_SECONDS after the last event."""

    def __init__(self, cmd: list[str]) -> None:
        super().__init__()
        self._cmd = cmd
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    # watchdog calls on_modified for most editors; on_created handles new files
    def on_modified(self, event) -> None:  # type: ignore[override]
        self._schedule(event)

    def on_created(self, event) -> None:  # type: ignore[override]
        self._schedule(event)

    def _schedule(self, event) -> None:  # type: ignore[override]
        if event.is_directory or _is_excluded(event.src_path):
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        run_verification_loop(self._cmd)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ShadowLoop — file watcher, test runner & auto-committer",
    )
    parser.add_argument(
        "--cmd",
        default="python -m unittest",
        help='Verification command to run (default: "python -m unittest")',
    )
    args = parser.parse_args()
    cmd: list[str] = shlex.split(args.cmd)

    watch_root = Path(".").resolve()

    print(f"\n{BOLD}ShadowLoop{RESET} — infrastructure monitor")
    print(f"  {DIM}Watch root :{RESET} {watch_root}")
    print(f"  {DIM}Command    :{RESET} {' '.join(cmd)}")
    print(f"  {DIM}Debounce   :{RESET} {DEBOUNCE_SECONDS}s")
    print(f"  {DIM}Excluded   :{RESET} {', '.join(sorted(EXCLUDED_DIRS))}")
    print(f"  {DIM}Stop with  :{RESET} Ctrl+C\n")

    handler = _DebounceHandler(cmd)
    observer = Observer()
    observer.schedule(handler, str(watch_root), recursive=True)
    observer.start()

    try:
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{BOLD}ShadowLoop stopped.{RESET}")
    finally:
        observer.stop()
        observer.join()
    sys.exit(0)


if __name__ == "__main__":
    main()
