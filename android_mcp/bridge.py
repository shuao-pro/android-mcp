import httpx
import json
import uuid
from typing import Any

from android_mcp.config import config

_command_history: list[dict[str, Any]] = []
MAX_HISTORY = 200


def get_history() -> list:
    return _command_history


async def _send(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    request_id = str(uuid.uuid4())[:8]
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }

    await _ensure_adb_forward()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{config.ANDROID_BASE_URL}/mcp",
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
                headers={"Content-Type": "application/json"},
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
            "error": f"Android device not reachable at {config.ANDROID_HOST}:{config.ANDROID_PORT}. "
                     "Ensure the Android MCP app is running and ADB forward is set up.",
        }
    except httpx.RemoteProtocolError:
        result = {
            "success": False,
            "error": "Android device disconnected unexpectedly. "
                     "The Shizuku service may have stopped. Restart the Android MCP app.",
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
    """Run an ADB command and return stdout."""
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


async def _adb_bytes(cmd, timeout=5.0):
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
    """Re-establish ADB forward if it dropped. Returns True if forward is active."""
    result = await _adb(["forward", "--list"], timeout=3)
    if f"tcp:{config.ANDROID_PORT}" in result:
        return True
    await _adb(["forward", f"tcp:{config.ANDROID_PORT}", f"tcp:{config.ANDROID_PORT}"], timeout=3)
    return True


async def health_check() -> dict[str, Any]:
    await _ensure_adb_forward()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{config.ANDROID_BASE_URL}/health",
                timeout=5.0,
            )
            data = resp.json()
            # Normalize: Android APK returns {"result": "ok"} (JSON-RPC style);
            # older versions return {"connected": true}. Accept both.
            if data.get("result") == "ok" or data.get("connected"):
                return {"connected": True, "shizuku_running": True}
            return {"connected": False, "error": "unexpected health response"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def get_device_info() -> dict[str, Any]:
    return await _send("system.info")


async def get_screenshot() -> dict[str, Any]:
    result = await _send("system.screenshot", {"quality": 80})
    # Normalize: Android APK returns image_base64 at top level;
    # tools expect {data: {base64: ...}} nested format.
    if result.get("success") and "image_base64" in result:
        result["data"] = {"base64": result.pop("image_base64")}
    return result


async def fast_screenshot():
    """Get screenshot via direct ADB screencap (3-5x faster than HTTP bridge)."""
    import base64
    raw = await _adb_bytes(["exec-out", "screencap", "-p"], timeout=3)
    if raw and raw[:4] == b'\\x89PNG':
        return {"success": True, "data": {"base64": base64.b64encode(raw).decode()}}
    return {"success": False, "error": "ADB screencap failed"}


async def shell(command: str, timeout: float = 30.0) -> dict[str, Any]:
    return await _send("shell.exec", {"command": command, "timeout": int(timeout)})


async def click(x: int, y: int) -> dict[str, Any]:
    return await _send("input.tap", {"x": x, "y": y})


async def long_click(x: int, y: int, duration: float = 1.0) -> dict[str, Any]:
    # Convert seconds to milliseconds for Android device
    if duration < 10:
        duration = duration * 1000
    return await _send("input.long_press", {"x": x, "y": y, "duration": int(duration)})


async def swipe(
    start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.3
) -> dict[str, Any]:
    # Convert seconds to milliseconds for Android device
    if duration < 10:
        duration = duration * 1000
    return await _send("input.swipe", {
        "x1": start_x, "y1": start_y,
        "x2": end_x, "y2": end_y,
        "duration": int(duration),
    })


async def drag(
    start_x: int, start_y: int, end_x: int, end_y: int,
    duration: float = 0.5, steps: int = 10,
) -> dict[str, Any]:
    # Convert seconds to milliseconds for Android device
    if duration < 10:
        duration = duration * 1000
    return await _send("input.drag", {
        "x1": start_x, "y1": start_y,
        "x2": end_x, "y2": end_y,
        "duration": int(duration), "steps": steps,
    })


async def type_text(text: str, clear: bool = False) -> dict[str, Any]:
    if clear:
        # Select all + delete before typing new text
        return await _send("input.text", {"text": text, "clear": True})
    return await _send("input.text", {"text": text})


async def press_key(key: str, longpress: bool = False) -> dict[str, Any]:
    return await _send("input.keyevent", {"key": key, "longpress": longpress})


async def press_keycode(keycode: int, longpress: bool = False) -> dict[str, Any]:
    return await _send("input.keyevent", {"keycode": keycode, "longpress": longpress})


async def open_app(package_name: str, activity: str = "") -> dict[str, Any]:
    return await _send("package.open", {
        "package": package_name,
        "activity": activity,
    })


async def close_app(package_name: str) -> dict[str, Any]:
    return await _send("package.close", {"package": package_name})


async def clear_app_data(package_name: str) -> dict[str, Any]:
    return await _send("package.clear_data", {"package": package_name})


async def install_app(apk_path: str, silent: bool = True, allow_downgrade: bool = False) -> dict[str, Any]:
    return await _send("package.install", {
        "apk_path": apk_path,
        "silent": silent,
        "allow_downgrade": allow_downgrade,
    })


async def uninstall_app(package_name: str, keep_data: bool = False) -> dict[str, Any]:
    return await _send("package.uninstall", {
        "package": package_name,
        "keep_data": keep_data,
    })


async def list_installed_apps(filter: str = "", include_system: bool = False) -> dict[str, Any]:
    return await _send("package.list", {
        "filter": filter,
        "include_system": include_system,
    })


async def get_current_app() -> dict[str, Any]:
    return await shell(
        "dumpsys window | grep mCurrentFocus | awk '{print $3}' | cut -d/ -f1"
    )


async def get_ui_hierarchy() -> dict[str, Any]:
    return await shell(
        "uiautomator dump /dev/stdout 2>/dev/null | grep -v 'UI hierchary'"
    )


async def read_file(path: str) -> dict[str, Any]:
    return await _send("file.read", {"path": path})


async def write_file(path: str, content: str, append: bool = False) -> dict[str, Any]:
    return await _send("file.write", {
        "path": path,
        "content": content,
        "append": append,
    })


async def list_files(path: str = "/sdcard") -> dict[str, Any]:
    return await _send("file.list", {"path": path})


async def file_stat(path: str) -> dict[str, Any]:
    return await _send("file.stat", {"path": path})


async def delete_file(path: str, recursive: bool = False) -> dict[str, Any]:
    return await _send("file.delete", {"path": path, "recursive": recursive})


async def get_system_setting(namespace: str, key: str) -> dict[str, Any]:
    return await _send("system.settings.get", {"namespace": namespace, "key": key})


async def put_system_setting(namespace: str, key: str, value: str) -> dict[str, Any]:
    return await _send("system.settings.put", {
        "namespace": namespace, "key": key, "value": value,
    })


async def get_battery_info() -> dict[str, Any]:
    return await get_device_info()


async def set_clipboard(text: str) -> dict[str, Any]:
    return await _send("system.clipboard.set", {"text": text})


async def get_clipboard() -> dict[str, Any]:
    return await _send("system.clipboard.get")


async def get_notifications() -> dict[str, Any]:
    return await _send("system.notification.list")


async def cancel_notification(package: str) -> dict[str, Any]:
    return await _send("system.notification.cancel", {"package": package})


async def start_activity(action: str, extra: dict[str, str] | None = None) -> dict[str, Any]:
    cmd = f"am start -a {action}"
    if extra:
        for k, v in extra.items():
            cmd += f" --es {k} '{v}'"
    return await shell(cmd)


async def reboot() -> dict[str, Any]:
    return await _send("device.reboot")


async def screen_on() -> dict[str, Any]:
    return await _send("device.screen.on")


async def screen_off() -> dict[str, Any]:
    return await _send("device.screen.off")
