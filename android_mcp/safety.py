"""Safety guard: classify high-risk Android operations and gate execution behind user consent.

This module provides a single source of truth for deciding whether an operation
is safe to run on the device. The MCP tool layer calls :func:`gate` before
executing risky operations; when ``SAFETY_MODE=confirm`` (the default) the user
is prompted through the MCP client's elicitation mechanism and the operation only
runs if they explicitly approve.

Supported SAFETY_MODE values (set in ``.env``):

- ``permissive`` — allow everything (no confirmation).
- ``confirm``    — high/medium-risk operations require interactive user approval.
- ``strict``     — high/medium-risk operations are always blocked.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from android_mcp.config import config


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --------------------------------------------------------------------------
# Shell command classification
# --------------------------------------------------------------------------

# Destructive / privileged operations that should never run unattended.
_HIGH_SHELL_PATTERNS: list[re.Pattern] = [
    # Recursive deletion
    re.compile(r"\brm\b[^;|&\n]*?\s(?:-[a-zA-Z]*[rf][a-zA-Z]*|--recursive)\b", re.I),
    # Raw writes to block devices / whole disks
    re.compile(r"\bdd\b[^;|&\n]*\bof=(?:/dev/|/sdcard\b)", re.I),
    # Filesystem (re)formatting / partitioning
    re.compile(r"\b(?:mkfs|fdisk|parted|wipefs|resize2fs|newfs)\b", re.I),
    # Reboot / power off
    re.compile(r"\b(?:reboot|shutdown|poweroff|halt)\b", re.I),
    # Package manager destructive operations
    re.compile(r"\bpm\s+(?:uninstall|clear|disable|disable-user|enable)\b", re.I),
    # System settings mutation
    re.compile(r"\bsettings\s+put\s+(?:secure|global|system)\b", re.I),
    # Root escalation / property tampering
    re.compile(r"\b(?:setprop|resetprop|magisk|su|sudo)\b", re.I),
    # Mounting / unmounting
    re.compile(r"\b(?:mount|umount)\b", re.I),
    # Redirection into protected partitions/dirs
    re.compile(r">\s*/(?:system|vendor|boot|recovery|root|etc|firmware|dev|proc|sys)(?:/|\b|$)", re.I),
    # tee targeting protected partitions/dirs
    re.compile(r"\btee\b[^|;&\n]*\s/(?:system|vendor|boot|recovery|root|etc|firmware)(?:/|\b)", re.I),
    # cp / mv with a protected path as the (final) target argument
    re.compile(r"\b(?:cp|mv)\b[^|;&\n]*\s/(?:system|vendor|boot|recovery|root|etc|firmware)(?:/\S*)?\s*$", re.I),
    # Privilege escalation via chmod/chown on sensitive paths
    re.compile(r"\b(?:chmod|chown)\b[^|;&\n]*\b(?:/system|/vendor|/boot|/data)\b", re.I),
]

# Moderately risky operations (disruptive but recoverable).
_MEDIUM_SHELL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bam\s+(?:force-stop|kill|kill-all)\b", re.I),
    re.compile(r"\b(?:kill|killall)\b", re.I),
    re.compile(r"\bpm\s+install\b", re.I),
    re.compile(r"\bdumpsys\s+battery\s+reset\b", re.I),
    re.compile(r"\binput\s+keyevent\s+(?:26|POWER)\b", re.I),
    re.compile(r"\brm\b", re.I),  # any (non-recursive) deletion
    re.compile(r"\b(?:mv|cp)\b[^|;&\n]*\b(?:/data|/system|/vendor)\b", re.I),
]


def classify_shell(command: str) -> Risk:
    """Classify a shell command by risk."""
    if not command or not command.strip():
        return Risk.LOW
    for pat in _HIGH_SHELL_PATTERNS:
        if pat.search(command):
            return Risk.HIGH
    for pat in _MEDIUM_SHELL_PATTERNS:
        if pat.search(command):
            return Risk.MEDIUM
    return Risk.LOW


# --------------------------------------------------------------------------
# File operation classification
# --------------------------------------------------------------------------

_PROTECTED_DIRS: tuple[str, ...] = (
    "/system", "/vendor", "/boot", "/recovery",
    "/dev", "/proc", "/sys", "/root", "/etc", "/firmware",
)


def classify_file_write(path: str) -> Risk:
    """Classify writing to a device path by risk."""
    p = (path or "").strip()
    if not p:
        return Risk.LOW
    if p.startswith("/data/local/tmp"):
        return Risk.LOW  # the app's own scratch space
    if p.startswith("/data/"):
        return Risk.HIGH  # /data/data, /data/system, ...
    for d in _PROTECTED_DIRS:
        if p == d or p.startswith(d + "/"):
            return Risk.HIGH
    return Risk.LOW


def classify_file_delete(path: str, recursive: bool = False) -> Risk:
    """Classify deleting a device path by risk."""
    if recursive:
        return Risk.HIGH
    return classify_file_write(path)


# --------------------------------------------------------------------------
# Confirmation gate
# --------------------------------------------------------------------------


class ConfirmRequest(BaseModel):
    """Elicitation schema: the user approves or rejects the operation."""

    approve: bool = Field(description="Set to true to approve execution of this operation.")


def _mode() -> str:
    return (config.SAFETY_MODE or "confirm").strip().lower()


async def gate(ctx: Any, risk: Risk, description: str) -> tuple[bool, str]:
    """Gate an operation. Returns ``(allowed, error_message)``.

    ``error_message`` is empty when allowed. When blocked, the caller should
    surface it to the agent/user and NOT execute the operation.
    """
    if risk == Risk.LOW:
        return True, ""

    mode = _mode()
    if mode == "permissive":
        return True, ""

    label = "High-risk" if risk == Risk.HIGH else "Sensitive"

    if mode == "strict":
        return False, f"Blocked by SAFETY_MODE=strict ({label}): {description}"

    # mode == "confirm"
    if ctx is None:
        return False, (
            f"{label} operation requires user confirmation but no interactive "
            f"MCP context is available: {description}"
        )

    try:
        result = await ctx.elicit(
            f"\u26a0\ufe0f {label} Android operation requested.\n\n"
            f"{description}\n\n"
            f"Approve execution on the device?",
            ConfirmRequest,
        )
    except Exception as e:
        return False, (
            f"{label} operation confirmation failed "
            f"({type(e).__name__}: {e}): {description}"
        )

    if getattr(result, "action", None) == "accept" and result.data is not None:
        if getattr(result.data, "approve", False):
            return True, ""

    return False, f"{label} operation not approved by the user: {description}"