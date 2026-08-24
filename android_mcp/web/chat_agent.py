"""AI Chat Agent — multi-step, closed-loop device control.

Translates a natural-language goal into a sequence of Android MCP tool calls.
The agent loop:

1. LLM decides the next action (a tool call, or "done").
2. The tool is executed (including long-running tasks via run_task_and_wait).
3. The result (and optionally a vision description of the screen) is fed back.
4. The LLM decides whether to continue or finish — up to ``max_steps``.

Single-shot behavior is preserved via :func:`process_message`, which delegates
to :func:`run_agent`.
"""

from typing import Any

from android_mcp.utils import parse_json_lenient

# ========== Tool Registry ==========

TOOL_REGISTRY: dict[str, tuple[callable, str]] = {}


def _register(name: str, description: str):
    """Decorator to register a tool for the AI agent."""
    def decorator(fn):
        TOOL_REGISTRY[name] = (fn, description)
        return fn
    return decorator


# ========== Tool Definitions ==========


@_register("shell", "Execute a shell command on the Android device with ADB/Shizuku/root privileges. Params: command (str), timeout (float, default 30).")
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


# ---- Long-running task tools ----

@_register("run_task_and_wait", "Run a long-running shell command and wait for completion. Params: command (str), timeout (float, default 0=unlimited), poll_interval (float, default 1.0), max_wait (float, default 600).")
async def _run_task_and_wait(command: str, timeout: float = 0, poll_interval: float = 1.0, max_wait: float = 600):
    from android_mcp.tools.tasks import tool_run_task_and_wait
    return await tool_run_task_and_wait(command, timeout, poll_interval, max_wait)


@_register("submit_task", "Submit a command to run in the background. Returns task_id. Params: command (str), timeout (float, default 0).")
async def _submit_task(command: str, timeout: float = 0):
    from android_mcp import bridge
    return await bridge.submit_task(command, timeout)


@_register("get_task_status", "Get the state of a background task. Params: task_id (str).")
async def _get_task_status(task_id: str):
    from android_mcp import bridge
    return await bridge.get_task_status(task_id)


@_register("get_task_result", "Get the final result of a background task. Params: task_id (str).")
async def _get_task_result(task_id: str):
    from android_mcp import bridge
    return await bridge.get_task_result(task_id)


@_register("cancel_task", "Cancel a running background task. Params: task_id (str).")
async def _cancel_task(task_id: str):
    from android_mcp import bridge
    return await bridge.cancel_task(task_id)


@_register("list_tasks", "List all background tasks on the device. No params.")
async def _list_tasks():
    from android_mcp import bridge
    return await bridge.list_tasks()


# ========== System Prompt ==========


def _build_agent_system_prompt() -> str:
    tools_text = ""
    for name, (_, desc) in TOOL_REGISTRY.items():
        tools_text += f"\n- **{name}**: {desc}"

    return f"""You are an AI assistant that controls an Android device. You can complete multi-step tasks by calling tools one at a time.

Each turn, respond with ONE JSON object in exactly one of these forms:

1. To perform an action: {{"tool": "tool_name", "params": {{...}}}}
2. To finish successfully: {{"done": true, "reply": "short summary of what you did"}}
3. To answer a question without any device action: {{"reply": "your answer"}}

Rules:
- For UI tasks, use click_element (AI vision finds and taps the element); take_screenshot when you need to see the current screen.
- For long-running commands (installs, large downloads, builds), use run_task_and_wait instead of shell.
- Params must match the exact parameter names and types listed for each tool.
- If a step fails, try an alternative approach rather than giving up.
- Keep going until the user's goal is achieved, then respond with done.

Available tools:{tools_text}

Respond ONLY with valid JSON. No markdown, no explanation."""


# ========== Result summarization ==========


def _summarize_result(tool_name: str, result: Any) -> str:
    """Turn a tool result into a compact text summary for the LLM context."""
    if not isinstance(result, dict):
        return str(result)[:2000]

    if result.get("success") is False:
        err = result.get("error") or result.get("message") or "failed"
        return f"ERROR: {err}"[:2000]

    if tool_name in ("take_screenshot", "get_screenshot"):
        data = result.get("data") or {}
        b64 = data.get("base64", "") or result.get("image_base64", "")
        return f"screenshot captured ({len(b64)} base64 chars)"

    if tool_name in ("shell", "run_task_and_wait"):
        out = result.get("stdout") or ""
        err = result.get("stderr") or ""
        state = result.get("state") or ""
        exit_code = result.get("exit_code")
        text = out or err or str(result)
        if state:
            text = f"[state={state} exit={exit_code}] " + text
        return text[:2000]

    if tool_name in ("find_element", "click_element"):
        if result.get("success") and result.get("data"):
            d = result["data"]
            if d.get("center_x") is not None:
                return f"found element at ({d.get('center_x')},{d.get('center_y')})"
        return str(result)[:2000]

    return str(result)[:2000]


# ========== LLM client ==========


def _get_llm_client():
    """Create an LLM client from config. Returns None if not configured."""
    from android_mcp.config import config
    from android_mcp.vision.clients import AnthropicVisionClient, OpenAIVisionClient

    if not config.VISION_API_KEY:
        return None

    provider = config.VISION_PROVIDER.lower().strip()
    model = config.VISION_MODEL or None

    if provider == "anthropic":
        return AnthropicVisionClient(
            api_key=config.VISION_API_KEY,
            model=model or "claude-sonnet-5",
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


async def _describe_screen(client) -> str:
    """Capture a screenshot and return a text description of the current screen."""
    from android_mcp import bridge

    try:
        shot = await bridge.get_screenshot()
        b64 = ""
        if isinstance(shot, dict):
            data = shot.get("data") or {}
            b64 = data.get("base64", "") or shot.get("image_base64", "")
        if not b64:
            return ""
        desc = await client.describe_screenshot(
            b64,
            "Briefly describe the current screen: which app/page is shown and the key visible elements.",
        )
        return (desc or "")[:1000]
    except Exception:
        return ""


# ========== Multi-step Agent ==========


async def run_agent(
    goal: str,
    history: list[dict] | None = None,
    max_steps: int = 10,
    visual: bool = True,
) -> dict[str, Any]:
    """Run the closed-loop agent until the goal is done or ``max_steps`` reached.

    Returns a dict with ``success``, ``reply``, and ``steps`` (list of steps).
    """
    client = _get_llm_client()
    if client is None:
        msg = (
            "AI Chat not configured. Set VISION_PROVIDER and VISION_API_KEY in .env "
            "to enable AI-powered device control.\n\n"
            "Supported providers: anthropic, openai, custom"
        )
        return {"success": False, "reply": msg, "error": msg}

    system_prompt = _build_agent_system_prompt()
    messages = list(history or [])
    messages.append({"role": "user", "content": goal})

    steps: list[dict[str, Any]] = []

    for i in range(max_steps):
        try:
            raw_text = await client.chat(system_prompt, messages)
        except Exception as e:
            msg = f"LLM request failed: {e}"
            return {"success": False, "reply": msg, "error": msg, "steps": steps}

        try:
            parsed = parse_json_lenient(raw_text)
        except Exception:
            return {
                "success": False,
                "reply": raw_text.strip(),
                "error": raw_text.strip(),
                "steps": steps,
            }

        # Finished?
        if parsed.get("done") or ("reply" in parsed and "tool" not in parsed):
            return {
                "success": True,
                "reply": parsed.get("reply") or "Done.",
                "steps": steps,
                "done": True,
            }

        tool_name = str(parsed.get("tool", "") or "")
        params = parsed.get("params", {}) or {}
        messages.append({"role": "assistant", "content": raw_text})

        if tool_name not in TOOL_REGISTRY:
            avail = ", ".join(TOOL_REGISTRY.keys())
            messages.append({"role": "user", "content": f"[system] unknown tool '{tool_name}'. Available tools: {avail}"})
            continue

        fn, _ = TOOL_REGISTRY[tool_name]
        try:
            result = await fn(**params)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        summary = _summarize_result(tool_name, result)
        steps.append({
            "step": i + 1,
            "tool": tool_name,
            "params": params,
            "ok": bool(isinstance(result, dict) and result.get("success")),
            "summary": summary,
        })
        messages.append({"role": "user", "content": f"[tool result for {tool_name}] {summary}"})

        # Optional visual verification between steps.
        if visual and tool_name not in ("take_screenshot", "get_screenshot"):
            screen_desc = await _describe_screen(client)
            if screen_desc:
                messages.append({"role": "user", "content": f"[current screen] {screen_desc}"})

    msg = f"Reached max_steps ({max_steps}) without completing the goal."
    return {"success": False, "reply": msg, "error": msg, "steps": steps}


async def process_message(user_text: str, history: list[dict] | None = None) -> dict[str, Any]:
    """Backward-compatible entry point — delegates to the multi-step agent."""
    return await run_agent(user_text, history)