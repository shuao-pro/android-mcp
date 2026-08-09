"""Bridge: system-level operations (settings, clipboard, notifications, intents)."""

from typing import Any

from android_mcp.bridge._core import _send
from android_mcp.bridge.device import get_device_info, shell
from android_mcp.utils import escape_shell_arg


async def get_system_setting(namespace: str, key: str) -> dict[str, Any]:
    """Read a system setting (namespace: system, global, secure)."""
    return await _send("system.settings.get", {"namespace": namespace, "key": key})


async def put_system_setting(namespace: str, key: str, value: str) -> dict[str, Any]:
    """Write a system setting (requires Shizuku)."""
    return await _send("system.settings.put", {
        "namespace": namespace, "key": key, "value": value,
    })


async def get_battery_info() -> dict[str, Any]:
    """Get battery level, charging status, temperature."""
    return await get_device_info()


async def set_clipboard(text: str) -> dict[str, Any]:
    """Set the device clipboard content."""
    return await _send("system.clipboard.set", {"text": text})


async def get_clipboard() -> dict[str, Any]:
    """Get the device clipboard content."""
    return await _send("system.clipboard.get")


async def get_notifications() -> dict[str, Any]:
    """Get recent notifications from the device."""
    return await _send("system.notification.list")


async def cancel_notification(package: str) -> dict[str, Any]:
    """Cancel notifications for a specific package."""
    return await _send("system.notification.cancel", {"package": package})


async def start_activity(
    action: str, extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Start an Android activity via am start."""
    cmd_parts = ["am", "start", "-a", action]
    if extra:
        for k, v in extra.items():
            cmd_parts.extend(["--es", k, v])
    return await shell(" ".join(escape_shell_arg(p) for p in cmd_parts))
