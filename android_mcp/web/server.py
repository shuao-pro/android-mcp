"""Web GUI server: FastAPI + WebSocket for device dashboard and AI chat."""

import asyncio
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from android_mcp import bridge
from android_mcp.config import config
from android_mcp.web.scrcpy_bridge import (
    is_scrcpy_installed,
    is_scrcpy_running,
    start_scrcpy,
    stop_scrcpy,
    start_stream,
    stop_stream,
    add_stream_client,
    remove_stream_client,
)

app = FastAPI(title="Android MCP Dashboard", version="2.0")

static_dir = os.path.join(os.path.dirname(__file__), "static")

_ws_clients: set[WebSocket] = set()


@app.get("/")
async def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/status")
async def api_status():
    health = await bridge.health_check()
    return health


@app.get("/api/history")
async def api_history():
    return bridge.get_history()


@app.get("/api/setup/status")
async def api_setup_status():
    """Check all prerequisites with detailed info for the setup wizard."""
    import shutil
    import subprocess
    import socket

    import os as _os
    project_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

    # Detect local network IP
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    mcp_port = config.MCP_PORT

    result = {
        "adb_installed": False,
        "adb_version": "",
        "adb_path": "",
        "adb_device": False,
        "adb_device_info": "",
        "adb_device_list": [],
        "android_service": False,
        "android_service_detail": {},
        "dotenv_exists": False,
        "dotenv_path": _os.path.join(project_root, ".env"),
        "vision_configured": False,
        "vision_provider": "",
        "server_address": f"http://{local_ip}:{mcp_port}/sse",
        "server_local": f"http://127.0.0.1:{mcp_port}/sse",
        "server_ip": local_ip,
    }

    # ADB check
    adb_path = shutil.which("adb")
    result["adb_installed"] = adb_path is not None
    result["adb_path"] = adb_path or ""

    if adb_path:
        try:
            proc = await asyncio.to_thread(
                subprocess.run, ["adb", "version"],
                capture_output=True, text=True, timeout=5
            )
            result["adb_version"] = proc.stdout.strip().split("\n")[0]
        except Exception:
            pass

        try:
            proc = await asyncio.to_thread(
                subprocess.run, ["adb", "devices", "-l"],
                capture_output=True, text=True, timeout=5
            )
            raw_lines = proc.stdout.strip().split("\n")[1:]
            devices = []
            for line in raw_lines:
                line = line.strip()
                if line and "offline" not in line:
                    parts = line.split()
                    device_id = parts[0] if parts else ""
                    product = ""
                    model = ""
                    for p in parts[1:]:
                        if p.startswith("product:"):
                            product = p.split(":", 1)[1]
                        if p.startswith("model:"):
                            model = p.split(":", 1)[1]
                    devices.append({"id": device_id, "product": product, "model": model})
            result["adb_device"] = len(devices) > 0
            result["adb_device_list"] = devices
            if devices:
                d = devices[0]
                parts = [d["id"]]
                if d["model"]:
                    parts.append(d["model"].replace("_", " "))
                if d["product"]:
                    parts.append(f"({d['product']})")
                result["adb_device_info"] = " ".join(parts)
        except Exception:
            pass

    # Android MCP service (Shizuku, port 18080) — fast-fail in 2s
    try:
        health = await asyncio.wait_for(bridge.health_check(), timeout=2.0)
    except asyncio.TimeoutError:
        health = {"connected": False, "error": "health check timed out"}
    except Exception:
        health = {"connected": False}
    result["android_service"] = health.get("connected", False)
    result["android_service_detail"] = {
        "shizuku_running": health.get("shizuku_running", False),
        "device_name": "",
        "android_version": "",
    }

    if health.get("connected"):
        try:
            info = await asyncio.wait_for(bridge.get_device_info(), timeout=3.0)
            if info.get("success") and info.get("data"):
                d = info["data"]
                result["android_service_detail"]["device_name"] = d.get("device_name", "")
                result["android_service_detail"]["android_version"] = d.get("android_version", "")
        except Exception:
            pass

    # MCP server status (SSE + Streamable HTTP on port 9000)
    # The API itself proves the MCP server is running.
    result["mcp_server_running"] = True
    result["mcp_server_port"] = config.MCP_PORT

    # .env
    result["dotenv_exists"] = _os.path.isfile(result["dotenv_path"])

    # Vision API
    result["vision_configured"] = bool(config.VISION_PROVIDER and config.VISION_API_KEY)
    result["vision_provider"] = config.VISION_PROVIDER or ""

    return {"success": True, "data": result}


# ========== Settings API (.env read/write) ==========

def _get_project_root():
    import os as _os
    return _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


def _read_env_file():
    """Read .env file and return key-value pairs. Returns empty dict if not found."""
    import os as _os
    env_path = _os.path.join(_get_project_root(), ".env")
    result = {}
    if _os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    result[key] = val
    return result


def _write_env_updates(updates: dict):
    """Update .env file with new values, preserving existing keys and comments."""
    import os as _os
    env_path = _os.path.join(_get_project_root(), ".env")

    # Read existing file
    if _os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []

    # Build set of keys to update
    update_keys = set(updates.keys())
    updated_keys = set()

    # Update existing lines in-place
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in update_keys:
            new_lines.append(f"{key}={updates[key]}\n")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # Append new keys that weren't in the file
    for key in update_keys - updated_keys:
        new_lines.append(f"{key}={updates[key]}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


@app.get("/api/settings")
async def api_get_settings():
    """Read vision API settings from .env."""
    env_data = _read_env_file()
    return {
        "success": True,
        "data": {
            "vision_provider": env_data.get("VISION_PROVIDER", ""),
            "vision_api_key": env_data.get("VISION_API_KEY", ""),
            "vision_api_base": env_data.get("VISION_API_BASE", ""),
            "vision_model": env_data.get("VISION_MODEL", ""),
        },
    }


@app.post("/api/settings")
async def api_save_settings(data: dict):
    """Save vision API settings to .env file."""
    body = data or {}
    updates = {}

    provider = body.get("vision_provider", "").strip()
    api_key = body.get("vision_api_key", "").strip()
    api_base = body.get("vision_api_base", "").strip()
    model = body.get("vision_model", "").strip()

    if provider:
        updates["VISION_PROVIDER"] = provider
    if api_key:
        updates["VISION_API_KEY"] = api_key
    if api_base:
        updates["VISION_API_BASE"] = api_base
    if model:
        updates["VISION_MODEL"] = model

    try:
        _write_env_updates(updates)
        # Reload config so changes take effect immediately
        import os as _os
        config.VISION_PROVIDER = updates.get("VISION_PROVIDER", config.VISION_PROVIDER)
        config.VISION_API_KEY = updates.get("VISION_API_KEY", config.VISION_API_KEY)
        config.VISION_API_BASE = updates.get("VISION_API_BASE", config.VISION_API_BASE)
        config.VISION_MODEL = updates.get("VISION_MODEL", config.VISION_MODEL)
        return {"success": True, "data": {"saved": list(updates.keys())}}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== scrcpy API ==========


@app.get("/api/scrcpy/status")
async def api_scrcpy_status():
    return {
        "success": True,
        "data": {
            "installed": is_scrcpy_installed(),
            "running": is_scrcpy_running(),
        },
    }


@app.post("/api/scrcpy/start")
async def api_scrcpy_start():
    result = start_scrcpy()
    return result


@app.post("/api/scrcpy/stop")
async def api_scrcpy_stop():
    result = stop_scrcpy()
    return result


# ========== Screen Stream WebSocket ==========


# ========== ADB Management API ==========


@app.get("/api/adb/devices")
async def api_adb_devices():
    """List all connected ADB devices with details."""
    import shutil
    import subprocess

    if not shutil.which("adb"):
        return {"success": False, "error": "adb not installed"}

    try:
        proc = subprocess.run(
            ["adb", "devices", "-l"], capture_output=True, text=True, timeout=5
        )
        lines = proc.stdout.strip().split("\n")[1:]
        devices = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            device_id = parts[0]
            status = "offline" if "offline" in line else "online"
            transport = "usb" if "usb:" in line else ("wireless" if ":" in device_id else "unknown")
            product = ""
            model = ""
            for p in parts[1:]:
                if p.startswith("product:"):
                    product = p.split(":", 1)[1]
                if p.startswith("model:"):
                    model = p.split(":", 1)[1].replace("_", " ")
            if status == "online":
                devices.append({
                    "id": device_id,
                    "status": status,
                    "transport": transport,
                    "model": model,
                    "product": product,
                })
        return {"success": True, "data": {"devices": devices, "count": len(devices)}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/adb/connect")
async def api_adb_connect(data: dict):
    """Connect to a device via TCP/IP."""
    import shutil
    import subprocess

    if not shutil.which("adb"):
        return {"success": False, "error": "adb not installed"}

    body = data or {}
    host = body.get("host", "").strip()
    port = body.get("port", "5555").strip()

    if not host:
        return {"success": False, "error": "host is required"}

    target = f"{host}:{port}"
    try:
        proc = subprocess.run(
            ["adb", "connect", target],
            capture_output=True, text=True, timeout=10
        )
        output = proc.stdout.strip() or proc.stderr.strip()
        success = "connected" in output.lower() or "already connected" in output.lower()
        return {"success": success, "data": {"output": output, "target": target}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/adb/disconnect")
async def api_adb_disconnect(data: dict):
    """Disconnect a wireless ADB device."""
    import shutil
    import subprocess

    if not shutil.which("adb"):
        return {"success": False, "error": "adb not installed"}

    body = data or {}
    target = body.get("target", "").strip()

    if not target:
        return {"success": False, "error": "target is required"}

    try:
        proc = subprocess.run(
            ["adb", "disconnect", target],
            capture_output=True, text=True, timeout=10
        )
        output = proc.stdout.strip() or proc.stderr.strip()
        return {"success": True, "data": {"output": output, "target": target}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/adb/tcpip")
async def api_adb_tcpip(data: dict):
    """Enable TCP/IP debugging on a USB-connected device."""
    import shutil
    import subprocess

    if not shutil.which("adb"):
        return {"success": False, "error": "adb not installed"}

    body = data or {}
    port = body.get("port", "5555").strip()

    try:
        proc = subprocess.run(
            ["adb", "tcpip", port],
            capture_output=True, text=True, timeout=10
        )
        output = proc.stdout.strip() or proc.stderr.strip()
        if "restarting" in output.lower() or proc.returncode == 0:
            return {"success": True, "data": {"output": output, "port": port}}
        return {"success": False, "error": output}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.websocket("/ws/screen")
async def ws_screen_stream(ws: WebSocket):
    await ws.accept()
    add_stream_client(ws)

    # Auto-start streaming if needed
    from android_mcp.web.scrcpy_bridge import _streaming
    if not _streaming:
        await start_stream()

    try:
        while True:
            # Keep connection alive, handle client pings
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("cmd") == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        remove_stream_client(ws)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({
                    "cmd": "error", "result": {"success": False, "error": "Invalid JSON"},
                }))
                continue

            cmd = msg.get("cmd", "")
            params = msg.get("params", {})

            result: dict = {"success": False, "error": "unknown command"}

            try:
                if cmd == "chat":
                    # AI Chat Agent
                    from android_mcp.web.chat_agent import process_message

                    user_text = msg.get("text", "")
                    history = msg.get("history", [])

                    try:
                        chat_result = await process_message(user_text, history)
                        await ws.send_text(json.dumps({
                            "cmd": "chat",
                            "result": chat_result,
                        }))
                    except Exception as e:
                        await ws.send_text(json.dumps({
                            "cmd": "chat",
                            "result": {"reply": f"Chat error: {e}", "error": True},
                        }))
                    continue  # don't send the generic response below

                elif cmd == "health":
                    result = await bridge.health_check()
                elif cmd == "device_info":
                    result = await bridge.get_device_info()
                elif cmd == "screenshot":
                    result = await bridge.get_screenshot()
                elif cmd == "shell":
                    result = await bridge.shell(**params)
                elif cmd == "click":
                    result = await bridge.click(**params)
                elif cmd == "long_click":
                    result = await bridge.long_click(**params)
                elif cmd == "swipe":
                    result = await bridge.swipe(**params)
                elif cmd == "type_text":
                    result = await bridge.type_text(**params)
                elif cmd == "press_key":
                    result = await bridge.press_key(**params)
                elif cmd == "open_app":
                    result = await bridge.open_app(**params)
                elif cmd == "close_app":
                    result = await bridge.close_app(**params)
                elif cmd == "battery":
                    result = await bridge.get_battery_info()
                elif cmd == "history":
                    result = {"history": bridge.get_history()}
            except Exception as e:
                result = {"success": False, "error": f"Command '{cmd}' failed: {e}"}

            try:
                await ws.send_text(json.dumps({"cmd": cmd, "result": result}))
            except Exception:
                break  # client disconnected, exit loop
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)


async def broadcast_status():
    """Broadcast device status to all connected WebSocket clients."""
    global _ws_clients
    while True:
        await asyncio.sleep(3)
        if _ws_clients:
            try:
                status = await bridge.health_check()
                msg = json.dumps({"type": "status", "data": status})
                dead = set()
                for ws in _ws_clients:
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead.add(ws)
                _ws_clients -= dead
            except Exception:
                pass


def mount_static():
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
