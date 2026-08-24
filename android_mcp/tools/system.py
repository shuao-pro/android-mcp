"""Tools: system-level operations (shell, settings, clipboard, notifications, intents)."""

import json
from typing import Dict, Any

from android_mcp import bridge
from android_mcp.tools.decorators import bridge_call


@bridge_call
async def tool_shell(command: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Execute shell command with ADB/Shizuku privileges."""
    return await bridge.shell(command, timeout)


@bridge_call
async def tool_get_system_setting(namespace: str, key: str) -> Dict[str, Any]:
    """Read system setting (namespace: system, global, secure)."""
    return await bridge.get_system_setting(namespace, key)


@bridge_call
async def tool_put_system_setting(
    namespace: str, key: str, value: str
) -> Dict[str, Any]:
    """Write system setting (requires Shizuku)."""
    return await bridge.put_system_setting(namespace, key, value)


@bridge_call
async def tool_set_clipboard(text: str) -> Dict[str, Any]:
    return await bridge.set_clipboard(text)


@bridge_call
async def tool_get_clipboard() -> Dict[str, Any]:
    return await bridge.get_clipboard()


@bridge_call
async def tool_get_notifications() -> Dict[str, Any]:
    return await bridge.get_notifications()


@bridge_call
async def tool_start_activity(action: str, extra: str = "{}") -> Dict[str, Any]:
    """Start Activity via Intent."""
    extra_dict = json.loads(extra) if extra else {}
    return await bridge.start_activity(action, extra_dict)

@bridge_call
async def tool_get_privilege_mode() -> Dict[str, Any]:
    """Get the active privilege mode/backend on the Android device (auto|shizuku|root)."""
    return await bridge.get_mode()


@bridge_call
async def tool_set_privilege_mode(mode: str) -> Dict[str, Any]:
    """Set the privilege mode on the Android device: auto, shizuku, or root.

    root mode runs shell commands as uid 0 via su (for rooted devices).
    """
    return await bridge.set_mode(mode)