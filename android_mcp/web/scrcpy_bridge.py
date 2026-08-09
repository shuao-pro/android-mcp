"""scrcpy integration: native mirroring + high-fps ADB screen streaming.

Requires: scrcpy (optional, for native window), ADB (for in-browser stream).
"""

import asyncio
import json
import logging
import shutil
import subprocess

from android_mcp import bridge

logger = logging.getLogger(__name__)

# ========== Native scrcpy ==========

SCRCPY_BIN = shutil.which("scrcpy") or "scrcpy"


class _ScrcpyManager:
    """Encapsulates scrcpy process and stream state (singleton)."""

    def __init__(self) -> None:
        self._scrcpy_proc: subprocess.Popen | None = None
        self._stream_clients: set = set()
        self._streaming: bool = False
        self._frame_task: asyncio.Task | None = None
        self._stream_fps: int = 15
        self._use_fast: bool = True

    # --- Native scrcpy ---

    def is_installed(self) -> bool:
        return shutil.which("scrcpy") is not None

    def is_running(self) -> bool:
        return self._scrcpy_proc is not None and self._scrcpy_proc.poll() is None

    def start(self) -> dict:
        if not self.is_installed():
            return {"success": False, "error": "scrcpy not installed"}
        if self.is_running():
            return {"success": False, "error": "scrcpy already running"}
        try:
            self._scrcpy_proc = subprocess.Popen(
                [SCRCPY_BIN, "--stay-awake", "--turn-screen-off"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return {"success": True, "message": "scrcpy started"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self) -> dict:
        if not self.is_running():
            return {"success": False, "error": "scrcpy not running"}
        try:
            assert self._scrcpy_proc is not None
            self._scrcpy_proc.terminate()
            try:
                self._scrcpy_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._scrcpy_proc.kill()
            self._scrcpy_proc = None
            return {"success": True, "message": "scrcpy stopped"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Screen streaming ---

    async def start_stream(self) -> None:
        if self._streaming:
            return
        self._streaming = True
        self._frame_task = asyncio.create_task(self._stream_loop())

    async def stop_stream(self) -> None:
        self._streaming = False
        if self._frame_task:
            self._frame_task.cancel()
            self._frame_task = None

    async def _stream_loop(self) -> None:
        """Continuously capture and broadcast screenshots at target FPS."""
        interval = 1.0 / self._stream_fps
        offline_warned = False
        fast_fail_count = 0

        while self._streaming:
            if not self._stream_clients:
                await asyncio.sleep(0.5)
                continue

            try:
                if self._use_fast and fast_fail_count < 3:
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
                        "fps": self._stream_fps,
                        "method": "adb" if (fast_fail_count == 0 and self._use_fast) else "http",
                    })
                    dead = set()
                    for ws in list(self._stream_clients):
                        try:
                            await ws.send_text(msg)
                        except Exception:
                            dead.add(ws)
                    self._stream_clients -= dead
                elif not offline_warned:
                    offline_warned = True
                    offline_msg = json.dumps({
                        "type": "status", "error": "device_offline",
                        "message": "Device not connected.",
                    })
                    dead = set()
                    for ws in list(self._stream_clients):
                        try:
                            await ws.send_text(offline_msg)
                        except Exception:
                            dead.add(ws)
                    self._stream_clients -= dead
            except Exception:
                pass

            await asyncio.sleep(max(0.01, interval))

    def add_client(self, ws) -> None:
        self._stream_clients.add(ws)

    def remove_client(self, ws) -> None:
        self._stream_clients.discard(ws)
        if not self._stream_clients:
            asyncio.create_task(self.stop_stream())

    @property
    def client_count(self) -> int:
        return len(self._stream_clients)


# Singleton instance
_manager = _ScrcpyManager()

# --- Module-level API (backward compatible) ---


def is_scrcpy_installed() -> bool:
    return _manager.is_installed()


def is_scrcpy_running() -> bool:
    return _manager.is_running()


def start_scrcpy() -> dict:
    return _manager.start()


def stop_scrcpy() -> dict:
    return _manager.stop()


async def start_stream() -> None:
    await _manager.start_stream()


async def stop_stream() -> None:
    await _manager.stop_stream()


def add_stream_client(ws) -> None:
    _manager.add_client(ws)


def remove_stream_client(ws) -> None:
    _manager.remove_client(ws)


def stream_client_count() -> int:
    return _manager.client_count
