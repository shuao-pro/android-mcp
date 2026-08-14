"""Shared console output helpers: ANSI colors + Windows UTF-8 safety.

Centralizes terminal formatting so the gateway CLI (gateway.py) and the
server banner (main.py) share one implementation, and prevents GBK mojibake
on Windows consoles.
"""

import os
import sys


def setup_utf8() -> None:
    """Reconfigure stdout/stderr to UTF-8 to avoid Windows GBK mojibake."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _colors_enabled() -> bool:
    """Disable ANSI colors when piped or explicitly turned off via NO_COLOR."""
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

if _colors_enabled():
    GREEN, RED, YELLOW, BLUE = _GREEN, _RED, _YELLOW, _BLUE
    CYAN, BOLD, DIM, RESET = _CYAN, _BOLD, _DIM, _RESET
else:
    GREEN = RED = YELLOW = BLUE = CYAN = BOLD = DIM = RESET = ""


def paint(text: str, color: str) -> str:
    """Wrap text in an ANSI color (no-op when colors are disabled)."""
    return f"{color}{text}{RESET}"


def ok(msg: str) -> None:
    print(f"{GREEN}{msg}{RESET}")


def err(msg: str) -> None:
    print(f"{RED}{msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}{msg}{RESET}")


def info(msg: str) -> None:
    print(f"{BLUE}{msg}{RESET}")
