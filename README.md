<div align="center">

<!-- TERMINAL RECORDING — replace the src URL below with your asciinema / terminalizer link -->
<!-- [![Demo](https://asciinema.org/a/REPLACE_WITH_YOUR_RECORDING_ID.svg)](https://asciinema.org/a/REPLACE_WITH_YOUR_RECORDING_ID) -->

<br/>

```
███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗██╗      ██████╗  ██████╗ ██████╗
██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║██║     ██╔═══██╗██╔═══██╗██╔══██╗
███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║██║     ██║   ██║██║   ██║██████╔╝
╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║██║     ██║   ██║██║   ██║██╔═══╝
███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝███████╗╚██████╔╝╚██████╔╝██║
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝
```

**A self-healing, autonomous test runner and version-control daemon.**  
*Write code. Break things. Watch ShadowLoop fix and commit them — automatically.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Watchdog](https://img.shields.io/badge/Watchdog-6.0.0-FF6B6B?style=for-the-badge)](https://pypi.org/project/watchdog/)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Zero Cost](https://img.shields.io/badge/Runtime-Zero--Cost-A855F7?style=for-the-badge)](https://openswarm.dev)
[![Status](https://img.shields.io/badge/Daemon-Active-06B6D4?style=for-the-badge&logo=statuspage&logoColor=white)](#)

</div>

---

## What is ShadowLoop?

ShadowLoop is a **single-file Python daemon** that watches your project directory in real time. The moment you save a file, it automatically runs your test suite. If the tests fail, it surfaces the error trace immediately so you can fix it. The instant they pass, it commits the working code to Git — no manual `git add`, no `git commit`, no forgotten staging.

> It's the missing link between your editor and your version history.

---

## Features

### `[1]` Self-Healing Loop

ShadowLoop monitors every file save in your repository. A **2-second debounce** absorbs rapid keystrokes from modern editors, then fires a single clean test run.

- **Failure** → prints a structured `[REPAIR LOOP ACTIVE]` panel with the last 50 lines of stderr
- **Success** → immediately transitions to the validation flow
- Handles any test framework — `pytest`, `unittest`, `nose2`, custom shell scripts

```
┌────────────────────────────────────────────────────────────┐
│  [REPAIR LOOP ACTIVE]  Tests failed — inspect errors below │
│  18:23:00                                                   │
└────────────────────────────────────────────────────────────┘
  FAIL: test_basic_assertion (test_logic.TestCoreLogic)
  AssertionError: 1 != 2 : Expected values to match but they do not.
```

### `[2]` Automated Version Control

When tests pass, ShadowLoop immediately executes a full Git commit cycle — no human required.

```
┌────────────────────────────────────────────────────────────┐
│  [VALIDATION PASSED]  Auto-committing changes…             │
│  18:23:11                                                   │
└────────────────────────────────────────────────────────────┘
[main 3f9a21c] shadowloop: automatic test pass
 1 file changed, 1 insertion(+), 1 deletion(-)
```

- Runs `git add -A` to stage all changes
- Commits with a structured message: `shadowloop: automatic test pass`
- Resolves `git` via `shutil.which()` with a Windows fallback — **works cross-platform**

### `[3]` Zero-Cost Runtime via OpenSwarm / Antigravity

ShadowLoop was designed and deployed entirely inside the **[OpenSwarm](https://openswarm.dev) / Antigravity** AI infrastructure — a zero-cost, zero-setup Python environment. No Docker. No virtual machines. No cloud bills. The bundled Python runtime at `openswarm/app-*/resources/python-env/python.exe` is all you need.

- No conda, no pyenv, no virtualenv required
- Runs as a persistent background daemon
- Compatible with AI-assisted repair workflows

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Or use the OpenSwarm bundled runtime |
| Git | Any | [git-scm.com](https://git-scm.com/download/win) — must be on `PATH` |
| watchdog | ≥ 4.0.0 | Installed via `requirements.txt` |

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/shadowloop.git
cd shadowloop
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

> **Windows (OpenSwarm runtime):**
> ```powershell
> & "C:\Users\<YOU>\AppData\Local\openswarm\app-1.4.2\resources\python-env\python.exe" -m pip install -r requirements.txt
> ```

**3. Initialize your Git identity** *(first time only)*

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

**4. Launch the daemon**

```bash
python -u shadowloop.py
```

> **Windows (OpenSwarm runtime):**
> ```powershell
> & "C:\Users\<YOU>\AppData\Local\openswarm\app-1.4.2\resources\python-env\python.exe" -u shadowloop.py
> ```

ShadowLoop is now **live**. Edit any file in the directory and watch the loop trigger automatically.

---

## Configuration

ShadowLoop accepts a single optional CLI argument to override the default test command.

```
usage: shadowloop.py [-h] [--cmd CMD]

options:
  -h, --help   show this help message and exit
  --cmd CMD    Verification command to run (default: "python -m unittest")
```

### Examples

```bash
# Default — Python unittest
python -u shadowloop.py

# pytest
python -u shadowloop.py --cmd "pytest"

# pytest with verbose output and specific directory
python -u shadowloop.py --cmd "pytest tests/ -v"

# Custom shell script
python -u shadowloop.py --cmd "bash run_tests.sh"
```

### Internal Constants

You can tune these values directly in `shadowloop.py`:

| Constant | Default | Description |
|---|---|---|
| `DEBOUNCE_SECONDS` | `2.0` | Seconds of silence before triggering the test run |
| `STDERR_TAIL_LINES` | `50` | Number of trailing error lines to display on failure |
| `EXCLUDED_DIRS` | `.git`, `.venv`, `__pycache__` | Directories ignored by the file watcher |

---

## How It Works

```
  ┌─────────────────────────────────────────────────────────┐
  │                    YOUR EDITOR                          │
  │                  (saves a file)                         │
  └───────────────────────┬─────────────────────────────────┘
                          │  filesystem event
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              WATCHDOG OBSERVER                          │
  │         on_modified / on_created fires                  │
  └───────────────────────┬─────────────────────────────────┘
                          │
                    (2s debounce)
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │              VERIFICATION COMMAND                       │
  │           python -m unittest  (or custom)               │
  └─────────┬───────────────────────────────┬───────────────┘
            │ exit code != 0                │ exit code == 0
            ▼                               ▼
  ┌──────────────────────┐       ┌──────────────────────────┐
  │  [REPAIR LOOP ACTIVE]│       │  [VALIDATION PASSED]     │
  │  Print stderr trace  │       │  git add -A              │
  │  Wait for next save  │       │  git commit -m "..."     │
  └──────────────────────┘       └──────────────────────────┘
```

---

## Project Structure

```
shadowloop/
├── shadowloop.py       # The entire daemon — single file, zero dependencies beyond watchdog
├── requirements.txt    # watchdog>=4.0.0
├── test_logic.py       # Example test file (used in the self-repair demo)
└── README.md           # This file
```

---

## Deploying From Scratch

The complete environment setup, from a bare machine to a running daemon, takes under 5 minutes:

```bash
# 1. Get the code
git clone https://github.com/YOUR_USERNAME/shadowloop.git && cd shadowloop

# 2. Install the single dependency
pip install -r requirements.txt

# 3. Init your repo identity
git config user.name "Your Name" && git config user.email "you@example.com"

# 4. Start the loop
python -u shadowloop.py
```

From this point forward, ShadowLoop handles the entire test-and-commit cycle autonomously.

---

## Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feat/my-feature`
5. Open a Pull Request

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

Built with the **ShadowLoop self-repair engine** and the **Antigravity / OpenSwarm** AI infrastructure.

*The code that fixes itself.*

</div>
