"""Core bridge: JSON-RPC transport layer to Android device."""

import json
import uuid
from typing import Any

import httpx

from android_mcp.config import config

_command_history: list[dict[str, Any]] = []
MAX_HISTORY = 200


def get_history() -> list[dict[str, Any]]:
    """Return the command history."""
    return _command_history


async def _send(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a JSON-RPC request to the Android device and return the result."""
    request_id = str(uuid.uuid4())[:8]
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }

    await _ensure_adb_forward()

    try:
        headers = {"Content-Type": "application/json"}
        if config.ANDROID_TOKEN:
            headers["X-MCP-Token"] = config.ANDROID_TOKEN

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{config.ANDROID_BASE_URL}/mcp",
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
                headers=headers,
            )
            raw_body = resp.text

            if resp.status_code != 200:
                result = {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {raw_body[:200]}",
                }
            elif not raw_body.strip():
                result = {"success": True}
            else:
                data = resp.json()

                if "error" in data:
                    err = data["error"]
                    result = {
                        "success": False,
                        "error": err.get("message", str(err)),
                        "code": err.get("code", -1),
                    }
                elif "result" in data:
                    r = data["result"]
                    if isinstance(r, dict):
                        result = r
                    else:
                        result = {"success": True, "data": r}
                else:
                    result = {"success": True}

    except httpx.ConnectError:
        result = {
            "success": False,
            "error": (
                f"Android device not reachable at {config.ANDROID_HOST}:{config.ANDROID_PORT}. "
                "Ensure the Android MCP app is running and ADB forward is set up."
            ),
        }
    except httpx.RemoteProtocolError:
        result = {
            "success": False,
            "error": (
                "Android device disconnected unexpectedly. "
                "The Shizuku service may have stopped. Restart the Android MCP app."
            ),
        }
    except httpx.TimeoutException:
        result = {
            "success": False,
            "error": f"Request to Android device timed out after {config.REQUEST_TIMEOUT}s.",
        }
    except httpx.HTTPStatusError as e:
        result = {
            "success": False,
            "error": f"Android device returned HTTP {e.response.status_code}: {e.response.text[:200]}",
        }
    except Exception as e:
        result = {
            "success": False,
            "error": f"Bridge error: {type(e).__name__}: {e}",
        }

    _command_history.append({
        "id": request_id,
        "method": method,
        "params": params,
        "result": result,
    })
    if len(_command_history) > MAX_HISTORY:
        _command_history.pop(0)

    return result


async def _adb(cmd: list[str], timeout: float = 5.0) -> str:
    """Run an ADB command and return stdout string."""
    import subprocess, shutil, asyncio

    adb = shutil.which("adb")
    if not adb:
        return ""
    try:
        proc = await asyncio.create_subprocess_exec(
            adb, *cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""


async def _adb_bytes(cmd: list[str], timeout: float = 5.0) -> bytes:
    """Run an ADB command and return raw stdout bytes."""
    import subprocess, shutil, asyncio

    adb = shutil.which("adb")
    if not adb:
        return b""
    try:
        proc = await asyncio.create_subprocess_exec(
            adb, *cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout
    except Exception:
        return b""


async def _ensure_adb_forward() -> bool:
    """Re-establish ADB forward if it dropped."""
    result = await _adb(["forward", "--list"], timeout=3)
    if f"tcp:{config.ANDROID_PORT}" in result:
        return True
    await _adb(["forward", f"tcp:{config.ANDROID_PORT}", f"tcp:{config.ANDROID_PORT}"], timeout=3)
    return True


def _to_millis(duration: float) -> int:
    """Convert a duration to milliseconds if it appears to be in seconds (value < 10)."""
    return int(duration * 1000) if duration < 10 else int(duration)
