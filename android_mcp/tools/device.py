"""Tools: device state queries (health, device info, battery, screenshot, UI hierarchy)."""

from typing import Dict, Any

from android_mcp import bridge


async def tool_health_check() -> Dict[str, Any]:
    try:
        return await bridge.health_check()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_device_info() -> Dict[str, Any]:
    try:
        return await bridge.get_device_info()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_battery_info() -> Dict[str, Any]:
    try:
        return await bridge.get_battery_info()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_take_screenshot() -> Dict[str, Any]:
    try:
        import base64
        import os
        import time
        from android_mcp.config import config

        result = await bridge.get_screenshot()
        if result.get("success") and result.get("data", {}).get("base64"):
            img_data = result["data"]["base64"]
            os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
            filename = f"screenshot_{int(time.time())}.png"
            filepath = os.path.join(config.SCREENSHOT_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_data))
            result["saved_path"] = filepath
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_get_ui_hierarchy() -> Dict[str, Any]:
    try:
        return await bridge.get_ui_hierarchy()
    except Exception as e:
        return {"success": False, "error": str(e)}
