"""Decorators for automatic error handling in MCP tool functions."""

import functools
from typing import Any


def bridge_call(func):
    """Decorator that wraps bridge calls with try/except -> {success, error}.

    Eliminates the repeated pattern:
        try:
            return await bridge.xxx(...)
        except Exception as e:
            return {"success": False, "error": str(e)}

    Usage:
        @bridge_call
        async def tool_open_app(package_name: str) -> dict:
            return await bridge.open_app(package_name)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> dict[str, Any]:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
    return wrapper
