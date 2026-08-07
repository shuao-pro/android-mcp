"""Bridge: device state queries (health, info, screenshot, shell, hierarchy)."""

from typing import Any

import httpx

from android_mcp.bridge._core import _adb_bytes, _ensure_adb_forward, _send
from android_mcp.config import config


async def health_check() -> dict[str, Any]:
    """Check Android device connection and Shizuku state."""
    await _ensure_adb_forward()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.ANDROID_BASE_URL}/health",
                timeout=5.0,
            )
            data = resp.json()
            if data.get("result") == "ok" or data.get("connected"):
                return {"connected": True, "shizuku_running": True}
            return {"connected": False, "error": "unexpected health response"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def get_device_info() -> dict[str, Any]:
    """Get device model, Android version, screen resolution, etc."""
    return await _send("system.info")


async def get_screenshot() -> dict[str, Any]:
    """Capture a screenshot via HTTP bridge (base64 PNG)."""
    result = await _send("system.screenshot", {"quality": 80})
    if result.get("success") and "image_base64" in result:
        result["data"] = {"base64": result.pop("image_base64")}
    return result


async def fast_screenshot() -> dict[str, Any]:
    """Capture screenshot via direct ADB screencap (3-5x faster than HTTP bridge)."""
    import base64

    raw = await _adb_bytes(["exec-out", "screencap", "-p"], timeout=3)
    if raw and raw[:4] == b"\x89PNG":
        return {"success": True, "data": {"base64": base64.b64encode(raw).decode()}}
    return {"success": False, "error": "ADB screencap failed"}


async def shell(command: str, timeout: float = 30.0) -> dict[str, Any]:
    """Execute a shell command with Shizuku privileges."""
    return await _send("shell.exec", {"command": command, "timeout": int(timeout)})


async def get_ui_hierarchy() -> dict[str, Any]:
    """Dump current screen UI hierarchy via uiautomator."""
    return await shell(
        "uiautomator dump /dev/stdout 2>/dev/null | grep -v 'UI hierchary'"
    )


async def reboot() -> dict[str, Any]:
    """Reboot the Android device."""
    return await _send("device.reboot")


async def screen_on() -> dict[str, Any]:
    """Turn the device screen on."""
    return await _send("device.screen.on")


async def screen_off() -> dict[str, Any]:
    """Turn the device screen off."""
    return await _send("device.screen.off")
