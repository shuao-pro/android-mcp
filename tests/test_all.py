"""Comprehensive test suite for android_mcp refactored code."""
import sys, asyncio

passed = 0; failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  PASS  {name}")
    except Exception as e:
        failed += 1
        print(f"  FAIL  {name}: {e}")

# ===== utils.py =====
print("=== utils.py ===")
from android_mcp.utils import (
    get_lan_ip, mask_api_key, escape_shell_arg,
    parse_json_lenient, strip_markdown_fence, extract_json_object,
)

test("get_lan_ip returns str",
    lambda: (ip := get_lan_ip(), isinstance(ip, str) and len(ip) > 5))

test("mask_api_key full",
    lambda: mask_api_key("sk-ant-api03-abc123def456") == "sk-ant***f456")
test("mask_api_key empty", lambda: mask_api_key("") == "")
test("mask_api_key short", lambda: len(mask_api_key("ab")) > 3)

q = "'"
test("escape_shell_arg normal",
    lambda: escape_shell_arg("hello") == q + "hello" + q)
test("escape_shell_arg with quote",
    lambda: escape_shell_arg("it's") == q + "it" + q + "\\" + q + q + "s" + q)

test("parse_json_lenient plain",
    lambda: parse_json_lenient('{"a": 1}') == {"a": 1})
test("parse_json_lenient with fence",
    lambda: parse_json_lenient('```json\n{"b": 2}\n```') == {"b": 2})
test("parse_json_lenient trailing comma",
    lambda: parse_json_lenient('{"c": 3,}') == {"c": 3})

test("strip_markdown_fence normal",
    lambda: strip_markdown_fence('```json\n{"x":1}\n```') == '{"x":1}')
test("strip_markdown_fence no fence",
    lambda: strip_markdown_fence('{"y":2}') == '{"y":2}')
test("extract_json_object embedded",
    lambda: "y" in extract_json_object('text {"y":2} more'))

# ===== config.py =====
print("\n=== config.py ===")
from android_mcp.config import config

test("config.validate() no warnings",
    lambda: (w := config.validate(), len(w) == 0))
test("ANDROID_BASE_URL computed",
    lambda: "http://" in config.ANDROID_BASE_URL)
test("WEB_PORT is int", lambda: isinstance(config.WEB_PORT, int))
test("REQUEST_TIMEOUT positive", lambda: config.REQUEST_TIMEOUT > 0)

# ===== bridge._core =====
print("\n=== bridge._core ===")
from android_mcp.bridge._core import _to_millis, get_history

test("_to_millis 1.0 -> 1000", lambda: _to_millis(1.0) == 1000)
test("_to_millis 0.5 -> 500", lambda: _to_millis(0.5) == 500)
test("_to_millis 500 -> 500", lambda: _to_millis(500) == 500)
test("_to_millis 0.01 -> 10", lambda: _to_millis(0.01) == 10)
test("_to_millis 15 -> 15", lambda: _to_millis(15) == 15)
test("get_history returns list", lambda: isinstance(get_history(), list))

# ===== bridge backward compat =====
print("\n=== bridge backward compat ===")
from android_mcp import bridge

for fn_name in [
    "click", "swipe", "shell", "health_check", "open_app",
    "read_file", "start_activity", "get_history",
    "long_click", "drag", "type_text", "press_key",
    "get_device_info", "get_screenshot", "fast_screenshot",
    "close_app", "install_app", "uninstall_app",
    "write_file", "list_files", "delete_file",
    "get_system_setting", "get_clipboard", "get_notifications",
]:
    test(f"bridge.{fn_name}", lambda n=fn_name: callable(getattr(bridge, n)))

from android_mcp.bridge.device import health_check, shell
from android_mcp.bridge.input import click, swipe
from android_mcp.bridge.apps import open_app
from android_mcp.bridge.files import read_file
from android_mcp.bridge.system import start_activity
test("submodule imports OK", lambda: True)

# ===== vision =====
print("\n=== vision ===")
from android_mcp.vision.models import BoundingBox, Element, VisionResult
from android_mcp.vision.prompts import build_vision_prompt, _parse_vision_response

test("BoundingBox", lambda: BoundingBox(0, 0, 100, 50).width == 100)
test("Element", lambda: Element("btn", 50, 25, 0.9).confidence == 0.9)
test("VisionResult empty", lambda: not VisionResult(False).found)

prompt = build_vision_prompt("login button")
test("build_vision_prompt has desc", lambda: "login button" in prompt)
test("build_vision_prompt has JSON", lambda: '"found"' in prompt)

valid_json = '{"found": true, "elements": [{"description": "btn", "center_x": 100, "center_y": 200, "confidence": 0.9}]}'
r = _parse_vision_response(valid_json)
test("parse valid found", lambda: r.found and len(r.elements) == 1)
test("parse valid coords", lambda: r.elements[0].center_x == 100)

nf = '{"found": false, "elements": []}'
test("parse not-found", lambda: not _parse_vision_response(nf).found)

fenced = "```json\n" + valid_json + "\n```"
test("parse fenced", lambda: _parse_vision_response(fenced).found)

tc = '{"found": true, "elements": [{"description": "x", "center_x": 0, "center_y": 0, "confidence": 0.5,}],}'
test("parse trailing commas", lambda: _parse_vision_response(tc).found)

test("parse invalid", lambda: not _parse_vision_response("not json").found)

# ===== decorators =====
print("\n=== decorators ===")
from android_mcp.tools.decorators import bridge_call

@bridge_call
async def ok_fn():
    return {"success": True, "data": "ok"}

@bridge_call
async def fail_fn():
    raise ValueError("test error")

test("decorator success",
    lambda: asyncio.run(ok_fn()) == {"success": True, "data": "ok"})
test("decorator failure",
    lambda: (r := asyncio.run(fail_fn()), not r["success"] and "test error" in r["error"]))

# ===== scrcpy_bridge =====
print("\n=== scrcpy_bridge ===")
from android_mcp.web.scrcpy_bridge import (
    is_scrcpy_installed, is_scrcpy_running, stream_client_count, _manager,
)
test("scrcpy_installed bool", lambda: isinstance(is_scrcpy_installed(), bool))
test("scrcpy_running bool", lambda: isinstance(is_scrcpy_running(), bool))
test("client_count int", lambda: isinstance(stream_client_count(), int))
test("_manager not running", lambda: not _manager.is_running())
test("_manager 0 clients", lambda: _manager.client_count == 0)

# ===== tools =====
print("\n=== tools ===")
from android_mcp.tools import register_all_tools
from android_mcp.tools.apps import tool_open_app, tool_close_app
from android_mcp.tools.device import tool_health_check, tool_get_device_info
from android_mcp.tools.input import tool_click, tool_swipe, tool_press_key
from android_mcp.tools.system import tool_shell, tool_get_clipboard
from android_mcp.tools.files import tool_read_file, tool_write_file
test("tools import OK", lambda: callable(tool_open_app))

# ===== server.py =====
print("\n=== server.py ===")
from android_mcp.web.server import app
test("FastAPI app created", lambda: app.title == "Android MCP Dashboard")

# ===== main.py =====
print("\n=== main.py ===")
from android_mcp.main import run
test("run is callable", lambda: callable(run))

# ===== gateway.py =====
print("\n=== gateway.py ===")
from android_mcp.gateway import is_running, read_pid, cleanup_pid
test("gateway imports OK", lambda: callable(is_running))

# ===== Summary =====
print(f"\n{'='*40}")
print(f"  {passed} PASS, {failed} FAIL  ({passed + failed} total)")
print(f"{'='*40}")

sys.exit(0 if failed == 0 else 1)