"""scrcpy integration: native mirroring + high-fps ADB screen streaming.

Native scrcpy window: launch/stop via buttons.
In-browser stream: ADB exec-out screencap @ 15fps -> WebSocket -> <img>.

Requires: scrcpy (optional, for native window), ADB (for in-browser stream).
"""

import asyncio
import base64
import json
import logging
import shutil
import subprocess
import time

from android_mcp import bridge

logger = logging.getLogger(__name__)

# --- Native scrcpy ---
_scrcpy_proc = None

SCRCPY_BIN = shutil.which("scrcpy") or "scrcpy"

def is_scrcpy_installed():
    return shutil.which("scrcpy") is not None

def is_scrcpy_running():
    return _scrcpy_proc is not None and _scrcpy_proc.poll() is None

def start_scrcpy():
    global _scrcpy_proc
    if not is_scrcpy_installed():
        return {"success": False, "error": "scrcpy not installed"}
    if is_scrcpy_running():
        return {"success": False, "error": "scrcpy already running"}
    try:
        _scrcpy_proc = subprocess.Popen(
            [SCRCPY_BIN, "--stay-awake", "--turn-screen-off"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return {"success": True, "message": "scrcpy started"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stop_scrcpy():
    global _scrcpy_proc
    if not is_scrcpy_running():
        return {"success": False, "error": "scrcpy not running"}
    try:
        _scrcpy_proc.terminate()
        try:
            _scrcpy_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _scrcpy_proc.kill()
        _scrcpy_proc = None
        return {"success": True, "message": "scrcpy stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- ADB Fast Screenshot Stream ---
_stream_clients = set()
_streaming = False
_frame_task = None
_stream_fps = 15
_use_fast = True  # True = ADB direct, False = HTTP bridge fallback

async def start_stream():
    global _streaming, _frame_task
    if _streaming:
        return
    _streaming = True
    _frame_task = asyncio.create_task(_stream_loop())

async def stop_stream():
    global _streaming, _frame_task
    _streaming = False
    if _frame_task:
        _frame_task.cancel()
        _frame_task = None

async def _stream_loop():
    """Continuously capture and broadcast screenshots at high FPS."""
    interval = 1.0 / _stream_fps
    offline_warned = False
    fast_fail_count = 0

    while _streaming:
        if not _stream_clients:
            await asyncio.sleep(0.5)
            continue

        try:
            # Try ADB direct screencap first (fast), fall back to HTTP bridge
            if _use_fast and fast_fail_count < 3:
                result = await bridge.fast_screenshot()
                if not result.get("success"):
                    fast_fail_count += 1
                    result = await bridge.get_screenshot()
                else:
                    fast_fail_count = 0
            else:
                result = await bridge.get_screenshot()

            if result.get("success") and result.get("data", {}).get("base64"):
                offline_warned = False
                msg = json.dumps({
                    "type": "frame",
                    "base64": result["data"]["base64"],
                    "fps": _stream_fps,
                    "method": "adb" if (fast_fail_count == 0 and _use_fast) else "http",
                })
                dead = set()
                for ws in list(_stream_clients):
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead.add(ws)
                _stream_clients -= dead
            elif not offline_warned:
                offline_warned = True
                offline_msg = json.dumps({
                    "type": "status", "error": "device_offline",
                    "message": "Device not connected.",
                })
                dead = set()
                for ws in list(_stream_clients):
                    try:
                        await ws.send_text(offline_msg)
                    except Exception:
                        dead.add(ws)
                _stream_clients -= dead
        except Exception:
            pass

        # Account for capture time to maintain target FPS
        await asyncio.sleep(max(0.01, interval))

def add_stream_client(ws):
    _stream_clients.add(ws)

def remove_stream_client(ws):
    _stream_clients.discard(ws)
    if not _stream_clients:
        asyncio.create_task(stop_stream())

def stream_client_count():
    return len(_stream_clients)