"""Tools: touch screen input (click, swipe, drag, type, key)."""

from typing import Dict, Any

from android_mcp import bridge


async def tool_click(x: int, y: int) -> Dict[str, Any]:
    try:
        return await bridge.click(x, y)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_long_click(x: int, y: int, duration: float = 1.0) -> Dict[str, Any]:
    try:
        return await bridge.long_click(x, y, duration)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_swipe(
    start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5
) -> Dict[str, Any]:
    try:
        return await bridge.swipe(start_x, start_y, end_x, end_y, duration)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_drag(
    start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5
) -> Dict[str, Any]:
    try:
        return await bridge.drag(start_x, start_y, end_x, end_y, duration)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_type_text(text: str, clear: bool = False) -> Dict[str, Any]:
    try:
        return await bridge.type_text(text, clear)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_press_key(key: str) -> Dict[str, Any]:
    try:
        return await bridge.press_key(key)
    except Exception as e:
        return {"success": False, "error": str(e)}
