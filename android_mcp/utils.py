"""Shared utility functions used across the Android MCP codebase."""

import re
import json as _json
import socket as _socket
from typing import Any


# ========== JSON / Markdown parsing ==========

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)
_TRAILING_COMMA_PATTERN = re.compile(r",\s*([}\]])")


def strip_markdown_fence(text: str) -> str:
    """Strip ```json ... ``` markdown fences from a string."""
    m = _FENCE_PATTERN.match(text.strip())
    return m.group(1).strip() if m else text.strip()


def extract_json_object(text: str) -> str:
    """Extract the first JSON object {...} from text, stripping fences."""
    raw = strip_markdown_fence(text)
    if not raw.startswith("{"):
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            raw = m.group(0)
    return raw


def parse_json_lenient(text: str) -> dict[str, Any]:
    """Parse JSON with lenient handling of markdown fences and trailing commas."""
    raw = extract_json_object(text)
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        cleaned = _TRAILING_COMMA_PATTERN.sub(r"\1", raw)
        return _json.loads(cleaned)


# ========== Network ==========

def get_lan_ip() -> str:
    """Detect the LAN IP address via UDP socket trick. Returns "127.0.0.1" on failure."""
    s = None
    try:
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        if s:
            try:
                s.close()
            except Exception:
                pass


# ========== String masking ==========

def mask_api_key(key: str) -> str:
    """Mask an API key: show first 6 and last 4 chars. Returns empty for empty input."""
    if not key:
        return ""
    if len(key) <= 10:
        return key[:2] + "***" + key[-2:]
    return key[:6] + "***" + key[-4:]


# ========== Shell escaping ==========

def escape_shell_arg(arg: str) -> str:
    """Escape a shell argument with single-quote wrapping."""
    return "'" + arg.replace("'", "'\\''") + "'"


# ========== Version ==========

def get_version() -> str:
    """Return the package version from the single source of truth."""
    from android_mcp import __version__

    return __version__
