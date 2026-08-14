"""Tools: vision model-based UI element recognition and clicking."""

import re
from typing import Dict, Any

from android_mcp import bridge
from android_mcp.vision import create_vision_client


async def tool_find_element(description: str) -> Dict[str, Any]:
    """Find UI element on screen using vision model — returns coordinates, no click."""
    try:
        client = create_vision_client()
        if client is None:
            return {
                "success": False,
                "error": (
                    "Vision model not configured. Set VISION_PROVIDER (anthropic/openai/custom), "
                    "VISION_API_KEY, and optionally VISION_MODEL/VISION_API_BASE in .env."
                ),
            }

        screenshot_result = await bridge.get_screenshot()
        if not screenshot_result.get("success"):
            return screenshot_result
        base64_image = screenshot_result["data"]["base64"]

        # Try to get screen dimensions for better accuracy
        screen_width = 0
        screen_height = 0
        try:
            device_info = await bridge.get_device_info()
            if device_info.get("success"):
                # screen_resolution is the raw `wm size` output, e.g.
                # "Physical size: 1080x2400" — extract the two integers.
                display = device_info.get("screen_resolution", "").strip()
                m = re.search(r"(\d+)\s*x\s*(\d+)", display)
                if m:
                    screen_width = int(m.group(1))
                    screen_height = int(m.group(2))
        except Exception:
            pass

        result = await client.analyze_screenshot(
            base64_image, description, screen_width, screen_height
        )

        return {
            "success": result.found,
            "data": {
                "found": result.found,
                "description": description,
                "screen_width": screen_width,
                "screen_height": screen_height,
                "elements": [
                    {
                        "description": elem.description,
                        "center_x": elem.center_x,
                        "center_y": elem.center_y,
                        "confidence": elem.confidence,
                        "bounds": (
                            {
                                "x": elem.bounds.x,
                                "y": elem.bounds.y,
                                "width": elem.bounds.width,
                                "height": elem.bounds.height,
                            }
                            if elem.bounds
                            else None
                        ),
                    }
                    for elem in result.elements
                ],
            },
            "error": result.error if not result.found else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_click_element(description: str) -> Dict[str, Any]:
    """Find and click a UI element using vision model — combines find + click."""
    try:
        find_result = await tool_find_element(description)

        if not find_result.get("success"):
            return find_result

        elements = find_result.get("data", {}).get("elements", [])
        if not elements:
            return {
                "success": False,
                "error": f"No element matching '{description}' found",
            }

        element = elements[0]
        x, y = element["center_x"], element["center_y"]
        click_result = await bridge.click(x, y)

        return {
            "success": click_result.get("success", False),
            "data": {
                "element_clicked": element,
                "click_coordinates": {"x": x, "y": y},
                "click_result": click_result,
                "all_candidates": elements if len(elements) > 1 else None,
                "screen_width": find_result["data"].get("screen_width", 0),
                "screen_height": find_result["data"].get("screen_height", 0),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
