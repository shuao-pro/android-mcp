"""Prompt builder and response parser for vision model interactions."""

import json
import re
from android_mcp.vision.models import BoundingBox, Element, VisionResult


def build_vision_prompt(
    description: str, screen_width: int = 0, screen_height: int = 0
) -> str:
    """Build a system prompt instructing the vision model to locate UI elements."""
    screen_info = ""
    if screen_width > 0 and screen_height > 0:
        screen_info = f" (screen resolution: {screen_width}x{screen_height} pixels)"

    return f"""You are a precision UI element locator for Android devices{screen_info}.

Your task: analyze the provided screenshot and locate the UI element matching the user's description.

Rules:
1. Examine the screenshot carefully. Identify ALL elements matching the description.
2. For each match, provide the exact pixel coordinates.
3. Coordinates: (0,0) is the top-left corner. Provide center_x and center_y in pixels.
4. If the element is NOT visible, return found: false.
5. If multiple elements match, return ALL of them, sorted by relevance/confidence.
6. Confidence should reflect how certain you are (0.0 to 1.0).
7. bounds should be the bounding box of the element: {{"x": left, "y": top, "width": w, "height": h}}.

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{
  "found": true,
  "elements": [
    {{
      "description": "brief description of this element",
      "center_x": 540,
      "center_y": 960,
      "confidence": 0.95,
      "bounds": {{"x": 100, "y": 900, "width": 880, "height": 120}}
    }}
  ]
}}

If the element is not found:
{{
  "found": false,
  "elements": []
}}"""


def _parse_vision_response(json_text: str) -> VisionResult:
    """Parse JSON response from a vision model into a VisionResult.

    Handles common model output quirks:
    - Markdown code fences (```json ... ```)
    - Trailing commas
    - Leading/trailing whitespace
    """
    raw = json_text.strip()

    # Strip markdown code fences if present
    fence_pattern = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)
    match = fence_pattern.match(raw)
    if match:
        raw = match.group(1).strip()

    # Try to extract JSON object if embedded in text
    if not raw.startswith("{"):
        obj_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if obj_match:
            raw = obj_match.group(0)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try removing trailing commas before last ] or }
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return VisionResult(
                found=False,
                raw_response=json_text,
                error=f"Failed to parse model response: {e}",
            )

    found = data.get("found", False)
    elements_data = data.get("elements", [])

    elements = []
    for elem in elements_data:
        bounds = None
        if "bounds" in elem and elem["bounds"]:
            b = elem["bounds"]
            bounds = BoundingBox(
                x=int(b.get("x", 0)),
                y=int(b.get("y", 0)),
                width=int(b.get("width", 0)),
                height=int(b.get("height", 0)),
            )

        elements.append(
            Element(
                description=elem.get("description", ""),
                center_x=int(elem.get("center_x", 0)),
                center_y=int(elem.get("center_y", 0)),
                confidence=float(elem.get("confidence", 0.0)),
                bounds=bounds,
            )
        )

    # Sort by confidence descending
    elements.sort(key=lambda e: e.confidence, reverse=True)

    return VisionResult(
        found=found,
        elements=elements,
        raw_response=json_text,
        error=None if found else data.get("error", "Element not found"),
    )
