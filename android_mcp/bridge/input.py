"""Bridge: touch input operations (click, swipe, drag, type, key)."""

from typing import Any

from android_mcp.bridge._core import _send, _to_millis


async def click(x: int, y: int) -> dict[str, Any]:
    """Tap at pixel coordinates."""
    return await _send("input.tap", {"x": x, "y": y})


async def long_click(x: int, y: int, duration: float = 1.0) -> dict[str, Any]:
    """Long-press at pixel coordinates."""
    return await _send("input.long_press", {
        "x": x, "y": y, "duration": _to_millis(duration),
    })


async def swipe(
    start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.3,
) -> dict[str, Any]:
    """Swipe from (start_x,start_y) to (end_x,end_y)."""
    return await _send("input.swipe", {
        "x1": start_x, "y1": start_y,
        "x2": end_x, "y2": end_y,
        "duration": _to_millis(duration),
    })


async def drag(
    start_x: int, start_y: int, end_x: int, end_y: int,
    duration: float = 0.5, steps: int = 10,
) -> dict[str, Any]:
    """Drag from (start_x,start_y) to (end_x,end_y)."""
    return await _send("input.drag", {
        "x1": start_x, "y1": start_y,
        "x2": end_x, "y2": end_y,
        "duration": _to_millis(duration), "steps": steps,
    })


async def type_text(text: str, clear: bool = False) -> dict[str, Any]:
    """Type text into the focused input field."""
    return await _send("input.text", {"text": text, "clear": clear})


async def press_key(key: str, longpress: bool = False) -> dict[str, Any]:
    """Press a device key by name (back, home, enter, etc.)."""
    return await _send("input.keyevent", {"key": key, "longpress": longpress})


async def press_keycode(keycode: int, longpress: bool = False) -> dict[str, Any]:
    """Press a device key by Android keycode."""
    return await _send("input.keyevent", {"keycode": keycode, "longpress": longpress})
