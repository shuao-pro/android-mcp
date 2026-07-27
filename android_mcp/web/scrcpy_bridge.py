"""scrcpy integration: native mirroring + high-fps WebSocket screen stream.

Requires scrcpy installed: https://github.com/Genymobile/scrcpy
(Arch: pacman -S scrcpy, Mac: brew install scrcpy, Win: scoop install scrcpy)
"""

import asyncio
import base64
import json
import logging
import shutil
import subprocess

from android_mcp import bridge

logger = logging.getLogger(__name__)

# State
_scrcpy_proc: subprocess.Popen | None = None
_stream_clients: set = set()
_streaming = False
_frame_task: asyncio.Task | None = None

SCRCPY_BIN = shutil.which("scrcpy") or "scrcpy"


def is_scrcpy_installed() -> bool:
    return shutil.which("scrcpy") is not None


def is_scrcpy_running() -> bool:
    return _scrcpy_proc is not None and _scrcpy_proc.poll() is None


def start_scrcpy() -> dict:
    """Launch native scrcpy window."""
    global _scrcpy_proc

    if not is_scrcpy_installed():
        return {"success": False, "error": "scrcpy not installed. Install from: https://github.com/Genymobile/scrcpy"}

    if is_scrcpy_running():
        return {"success": False, "error": "scrcpy is already running"}

    try:
        _scrcpy_proc = subprocess.Popen(
            [SCRCPY_BIN, "--stay-awake", "--turn-screen-off"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"success": True, "message": "scrcpy started"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_scrcpy() -> dict:
    """Stop the native scrcpy process."""
    global _scrcpy_proc

    if not is_scrcpy_running():
        return {"success": False, "error": "scrcpy is not running"}

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


# ========== WebSocket Frame Streaming ==========


async def start_stream():
    """Start high-fps screenshot streaming to WebSocket clients."""
    global _streaming, _frame_task

    if _streaming:
        return

    _streaming = True
    _frame_task = asyncio.create_task(_stream_loop())


async def stop_stream():
    """Stop screenshot streaming."""
    global _streaming, _frame_task

    _streaming = False
    if _frame_task:
        _frame_task.cancel()
        _frame_task = None


async def _stream_loop():
    """Continuously capture and broadcast screenshots."""
    fps = 10
    interval = 1.0 / fps
    _offline_warned = False

    while _streaming:
        try:
            if _stream_clients:
                result = await bridge.get_screenshot()
                if result.get("success") and result.get("data", {}).get("base64"):
                    _offline_warned = False
                    msg = json.dumps({
                        "type": "frame",
                        "base64": result["data"]["base64"],
                    })
                    dead = set()
                    for ws in _stream_clients:
                        try:
                            await ws.send_text(msg)
                        except Exception:
                            dead.add(ws)
                    _stream_clients -= dead
                elif not _offline_warned:
                    # Send one offline notice, then keep connection alive with pings
                    _offline_warned = True
                    offline_msg = json.dumps({
                        "type": "status",
                        "error": "device_offline",
                        "message": "Device not connected. Start Shizuku + Android MCP app on your phone.",
                    })
                    dead = set()
                    for ws in _stream_clients:
                        try:
                            await ws.send_text(offline_msg)
                        except Exception:
                            dead.add(ws)
                    _stream_clients -= dead
                else:
                    # Keep connection alive with heartbeat
                    dead = set()
                    for ws in _stream_clients:
                        try:
                            await ws.send_text(json.dumps({"type": "pong"}))
                        except Exception:
                            dead.add(ws)
                    _stream_clients -= dead
        except Exception:
            pass

        await asyncio.sleep(interval)


def add_stream_client(ws):
    _stream_clients.add(ws)


def remove_stream_client(ws):
    _stream_clients.discard(ws)
    # Auto-stop streaming when no clients
    if not _stream_clients:
        asyncio.create_task(stop_stream())


def stream_client_count() -> int:
    return len(_stream_clients)
