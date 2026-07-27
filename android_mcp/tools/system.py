"""Tools: system-level operations (shell, settings, clipboard, notifications, intents)."""

from typing import Dict, Any

from android_mcp import bridge


async def tool_shell(command: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Execute shell command with ADB/Shizuku privileges."""
    try:
        return await bridge.shell(command, timeout)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_system_setting(namespace: str, key: str) -> Dict[str, Any]:
    """Read system setting (namespace: system, global, secure)."""
    try:
        return await bridge.get_system_setting(namespace, key)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_put_system_setting(
    namespace: str, key: str, value: str
) -> Dict[str, Any]:
    """Write system setting (requires Shizuku)."""
    try:
        return await bridge.put_system_setting(namespace, key, value)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_set_clipboard(text: str) -> Dict[str, Any]:
    try:
        return await bridge.set_clipboard(text)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_clipboard() -> Dict[str, Any]:
    try:
        return await bridge.get_clipboard()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_notifications() -> Dict[str, Any]:
    try:
        return await bridge.get_notifications()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_start_activity(action: str, extra: str = "{}") -> Dict[str, Any]:
    """Start Activity via Intent."""
    try:
        import json
        extra_dict = json.loads(extra) if extra else {}
        return await bridge.start_activity(action, extra_dict)
    except Exception as e:
        return {"success": False, "error": str(e)}
