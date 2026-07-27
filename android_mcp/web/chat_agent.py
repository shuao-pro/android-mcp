"""AI Chat Agent — translates natural language to Android MCP tool calls.

Uses the configured vision/LLM provider (Anthropic/OpenAI/custom) to interpret
user requests and execute the appropriate device control tools.
"""

import json
import re
from typing import Any

from android_mcp.vision.clients import AnthropicVisionClient, OpenAIVisionClient

# ========== Tool Registry ==========
# Maps tool names to (function, description) for the LLM system prompt

TOOL_REGISTRY: dict[str, tuple[callable, str]] = {}


def _register(name: str, description: str):
    """Decorator to register a tool for the AI agent."""

    def decorator(fn):
        TOOL_REGISTRY[name] = (fn, description)
        return fn

    return decorator


# ========== Tool Definitions ==========


@_register("shell", "Execute a shell command on the Android device with ADB/Shizuku privileges. Params: command (str), timeout (float, default 30).")
async def _shell(command: str, timeout: float = 30.0):
    from android_mcp import bridge
    return await bridge.shell(command, timeout)


@_register("take_screenshot", "Take a screenshot of the device screen. Returns base64-encoded PNG. No params needed.")
async def _take_screenshot():
    from android_mcp import bridge
    return await bridge.get_screenshot()


@_register("click", "Tap at specific pixel coordinates. Params: x (int), y (int).")
async def _click(x: int, y: int):
    from android_mcp import bridge
    return await bridge.click(x, y)


@_register("long_click", "Long-press at specific pixel coordinates. Params: x (int), y (int), duration (float, default 1.0).")
async def _long_click(x: int, y: int, duration: float = 1.0):
    from android_mcp import bridge
    return await bridge.long_click(x, y, duration)


@_register("swipe", "Swipe from one coordinate to another. Params: start_x, start_y, end_x, end_y (int), duration (float, default 0.5).")
async def _swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5):
    from android_mcp import bridge
    return await bridge.swipe(start_x, start_y, end_x, end_y, duration)


@_register("type_text", "Type text into the currently focused input field. Params: text (str), clear (bool, default false).")
async def _type_text(text: str, clear: bool = False):
    from android_mcp import bridge
    return await bridge.type_text(text, clear)


@_register("press_key", "Press a device key. Params: key (str) — one of: back, home, recent, power, volume_up, volume_down, enter, delete, space.")
async def _press_key(key: str):
    from android_mcp import bridge
    return await bridge.press_key(key)


@_register("open_app", "Open an app by package name. Params: package_name (str) — e.g. com.android.settings.")
async def _open_app(package_name: str):
    from android_mcp import bridge
    return await bridge.open_app(package_name)


@_register("close_app", "Force-stop an app by package name. Params: package_name (str).")
async def _close_app(package_name: str):
    from android_mcp import bridge
    return await bridge.close_app(package_name)


@_register("get_current_app", "Get the currently foreground app package name. No params.")
async def _get_current_app():
    from android_mcp import bridge
    return await bridge.get_current_app()


@_register("list_installed_apps", "List all installed apps on the device. No params.")
async def _list_installed_apps():
    from android_mcp import bridge
    return await bridge.list_installed_apps()


@_register("get_device_info", "Get device details: model, Android version, screen resolution, current app. No params.")
async def _get_device_info():
    from android_mcp import bridge
    return await bridge.get_device_info()


@_register("get_battery_info", "Get battery level, charging status, temperature. No params.")
async def _get_battery_info():
    from android_mcp import bridge
    return await bridge.get_battery_info()


@_register("find_element", "Find a UI element on screen using AI vision. Returns coordinates. Params: description (str) — e.g. 'the login button', 'search icon'.")
async def _find_element(description: str):
    from android_mcp.tools.vision import tool_find_element
    return await tool_find_element(description)


@_register("click_element", "Find AND click a UI element using AI vision in one step. Params: description (str) — e.g. 'the Submit button'.")
async def _click_element(description: str):
    from android_mcp.tools.vision import tool_click_element
    return await tool_click_element(description)


@_register("read_file", "Read a file from the device (supports restricted directories). Params: path (str).")
async def _read_file(path: str):
    from android_mcp import bridge
    return await bridge.read_file(path)


@_register("write_file", "Write content to a file on the device. Params: path (str), content (str).")
async def _write_file(path: str, content: str):
    from android_mcp import bridge
    return await bridge.write_file(path, content)


@_register("set_clipboard", "Set the device clipboard content. Params: text (str).")
async def _set_clipboard(text: str):
    from android_mcp import bridge
    return await bridge.set_clipboard(text)


@_register("get_clipboard", "Get the device clipboard content. No params.")
async def _get_clipboard():
    from android_mcp import bridge
    return await bridge.get_clipboard()


@_register("get_notifications", "Get recent notifications from the device. No params.")
async def _get_notifications():
    from android_mcp import bridge
    return await bridge.get_notifications()


# ========== System Prompt Builder ==========


def _build_system_prompt() -> str:
    """Build the system prompt listing all available tools."""
    tools_text = ""
    for name, (_, desc) in TOOL_REGISTRY.items():
        tools_text += f"\n- **{name}**: {desc}"

    return f"""You are an AI assistant that controls an Android device. You have access to device control tools.

When the user asks you to do something on their phone, respond with a JSON object containing the tool to call.

Rules:
1. If the user just wants to chat or ask a question, reply with: {{"reply": "your text response"}}
2. If the user wants you to DO something on the device, respond with: {{"tool": "tool_name", "params": {{...}}}}
3. For visual tasks (clicking buttons, finding elements on screen), use click_element which uses AI vision.
4. For pressing system keys, use press_key (e.g. home, back, recent).
5. Always check the device state first if needed (get_device_info).
6. Use shell commands for complex operations not covered by other tools.
7. Params must match the exact parameter names and types listed for each tool.

Available tools:{tools_text}

Respond ONLY with valid JSON. No markdown, no explanation."""


# ========== Response Parser ==========


def _parse_llm_response(text: str) -> dict[str, Any]:
    """Parse LLM response into {tool, params} or {reply}."""
    raw = text.strip()

    # Strip markdown fences
    fence = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)
    m = fence.match(raw)
    if m:
        raw = m.group(1).strip()

    # Extract JSON object
    if not raw.startswith("{"):
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            raw = m.group(0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try cleaning trailing commas
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"reply": raw}


# ========== Main Agent ==========


def _get_llm_client():
    """Create an LLM client from config. Returns None if not configured."""
    from android_mcp.config import config

    if not config.VISION_API_KEY:
        return None

    provider = config.VISION_PROVIDER.lower().strip()
    model = config.VISION_MODEL or None

    if provider == "anthropic":
        return AnthropicVisionClient(
            api_key=config.VISION_API_KEY,
            model=model or "claude-sonnet-5-20251001",
        )
    elif provider == "openai":
        return OpenAIVisionClient(
            api_key=config.VISION_API_KEY,
            model=model or "gpt-4o",
        )
    elif provider == "custom":
        return OpenAIVisionClient(
            api_key=config.VISION_API_KEY,
            model=model or "gpt-4o",
            base_url=config.VISION_API_BASE or None,
        )
    return None


async def process_message(user_text: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Process a user message, call the LLM, and execute any tool.

    Args:
        user_text: The user's natural language request.
        history: Previous conversation turns (optional).

    Returns:
        dict with 'reply' (str) and optional 'tool_result' if a tool was called.
    """
    client = _get_llm_client()
    if client is None:
        return {
            "reply": (
                "AI Chat not configured. Set VISION_PROVIDER and VISION_API_KEY in .env "
                "to enable AI-powered device control.\n\n"
                "Supported providers: anthropic, openai, custom"
            ),
            "error": True,
        }

    system_prompt = _build_system_prompt()

    # Build messages
    messages = history or []
    messages.append({"role": "user", "content": user_text})

    # For Anthropic, system is separate; for OpenAI, it's a message
    from android_mcp.config import config
    provider = config.VISION_PROVIDER.lower().strip()

    if provider == "anthropic":
        # Use Anthropic-specific format via the client
        import httpx, json as _json

        payload = {
            "model": getattr(client, "model", "claude-sonnet-5-20251001"),
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {"role": m["role"], "content": m["content"]} for m in messages[-10:]  # last 10 turns
            ],
        }

        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={
                    "x-api-key": config.VISION_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = "".join(
                b.get("text", "")
                for b in data.get("content", [])
                if b.get("type") == "text"
            )
    else:
        # OpenAI-compatible
        import httpx, json as _json

        openai_messages = [{"role": "system", "content": system_prompt}]
        openai_messages.extend(
            {"role": m["role"], "content": m["content"]} for m in messages[-10:]
        )

        base_url = (
            config.VISION_API_BASE.rstrip("/") + "/chat/completions"
            if config.VISION_API_BASE
            else "https://api.openai.com/v1/chat/completions"
        )

        payload = {
            "model": config.VISION_MODEL or "gpt-4o",
            "max_tokens": 1024,
            "messages": openai_messages,
        }

        async with httpx.AsyncClient() as http:
            resp = await http.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {config.VISION_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]

    # Parse LLM response
    parsed = _parse_llm_response(raw_text)

    # If it's just a text reply, return it
    if "reply" in parsed and "tool" not in parsed:
        return {"reply": parsed["reply"]}

    # Execute tool
    tool_name = parsed.get("tool", "")
    params = parsed.get("params", {})

    if tool_name not in TOOL_REGISTRY:
        return {
            "reply": f"I tried to use '{tool_name}' but it's not available. Available tools: {', '.join(TOOL_REGISTRY.keys())}",
            "error": True,
        }

    fn, _ = TOOL_REGISTRY[tool_name]

    try:
        result = await fn(**params)
        return {
            "reply": parsed.get("reply", f"Executed {tool_name}"),
            "tool_called": tool_name,
            "tool_params": params,
            "tool_result": result,
        }
    except Exception as e:
        return {
            "reply": f"Failed to execute {tool_name}: {e}",
            "tool_called": tool_name,
            "error": True,
        }
