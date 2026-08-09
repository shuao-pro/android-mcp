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
