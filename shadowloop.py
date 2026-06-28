#!/usr/bin/env python3
"""
shadowloop.py
─────────────
Monitors the current directory for file changes, runs unit tests,
and auto-commits when tests pass.

Usage:
    python shadowloop.py [--cmd "python -m unittest"]
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ── Configuration ────────────────────────────────────────────────────────────

EXCLUDED_DIRS: frozenset[str] = frozenset({".git", ".venv", "__pycache__"})
DEBOUNCE_SECONDS: float = 2.0

# Resolve git at import time; fall back to known Windows install path
GIT_EXE: str = (
    shutil.which("git")
    or r"C:\Program Files\Git\cmd\git.exe"
)

# ── ANSI helpers ─────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD  = "\033[1m"
RED   = "\033[31m"
GREEN = "\033[32m"
DIM   = "\033[2m"


def _is_excluded(path: str) -> bool:
    """Return True if any component of *path* is an excluded directory."""
    return any(part in EXCLUDED_DIRS for part in Path(path).parts)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def run_verification_loop(cmd: list[str], watch_root: Path) -> None:
    """Execute the verification command and react to its result."""
    result = _run(cmd)

    if result.returncode != 0:
        # ── Failure path: minimal red warning, isolate the error ──────────
        err = (result.stderr or result.stdout or "").strip()
        # Keep only the last meaningful line (traceback tail or assertion)
        lines = [l for l in err.splitlines() if l.strip()]
        tail = lines[-1] if lines else "tests failed (no output)"
        print(f"\n{RED}{BOLD}✗ Tests failed:{RESET} {RED}{tail}{RESET}\n")

    else:
        # ── Success path: autonomous git add . && git commit ───────────────
        add = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=watch_root)
        if add.returncode != 0:
            print(f"{RED}git add failed:{RESET} {add.stderr.strip()}\n")
            return

        commit = subprocess.run(
            ["git", "commit", "-m", "shadowloop: automatic test pass"],
            capture_output=True, text=True, cwd=watch_root
        )
        if commit.returncode == 0:
            print(f"\n{GREEN}{BOLD}[AUTONOMOUS COMMIT EXECUTED]{RESET} {commit.stdout.strip()}\n")
        else:
            # Gracefully handle "nothing to commit"
            msg = (commit.stdout or commit.stderr or "").strip()
            print(f"\n{YELLOW}{msg}{RESET}\n")


# ── Watchdog handler ─────────────────────────────────────────────────────────

class _DebounceHandler(FileSystemEventHandler):
    """Debounced handler — waits DEBOUNCE_SECONDS after the last event."""

    def __init__(self, cmd: list[str], watch_root: Path) -> None:
        super().__init__()
        self._cmd = cmd
        self._watch_root = watch_root
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
        run_verification_loop(self._cmd, self._watch_root)


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ShadowLoop — file watcher, test runner & auto-committer",
    )
    parser.add_argument(
        "--cmd",
        default="python -m unittest",
        help='Verification command to run (default: "python -m unittest")',
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Target project directory to watch (default: current directory)",
    )
    args = parser.parse_args()
    cmd: list[str] = shlex.split(args.cmd)
    watch_root = Path(args.path).resolve()

    print(f"{BOLD}ShadowLoop{RESET} — watching {watch_root}")
    print(f"  {DIM}Command  :{RESET} {' '.join(cmd)}")
    print(f"  {DIM}Debounce :{RESET} {DEBOUNCE_SECONDS}s")
    print(f"  {DIM}Excluded :{RESET} {', '.join(sorted(EXCLUDED_DIRS))}")
    print(f"  {DIM}Stop     :{RESET} Ctrl+C\n")

    handler = _DebounceHandler(cmd, watch_root)
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
