"""MCP tools package — organized by domain.

Usage:
    from android_mcp.tools import register_all_tools
    mcp = FastMCP("server")
    register_all_tools(mcp)
"""

from typing import Dict, Any

from mcp.server.fastmcp import Context

from android_mcp import safety
from android_mcp.tools.device import (
    tool_health_check,
    tool_get_device_info,
    tool_get_battery_info,
    tool_take_screenshot,
    tool_get_ui_hierarchy,
)
from android_mcp.tools.input import (
    tool_click,
    tool_long_click,
    tool_swipe,
    tool_drag,
    tool_type_text,
    tool_press_key,
)
from android_mcp.tools.apps import (
    tool_open_app,
    tool_close_app,
    tool_clear_app_data,
    tool_install_app,
    tool_uninstall_app,
    tool_get_current_app,
    tool_list_installed_apps,
)
from android_mcp.tools.system import (
    tool_shell,
    tool_get_system_setting,
    tool_put_system_setting,
    tool_set_clipboard,
    tool_get_clipboard,
    tool_get_notifications,
    tool_start_activity,
    tool_get_privilege_mode,
    tool_set_privilege_mode,
)
from android_mcp.tools.files import (
    tool_read_file,
    tool_write_file,
)
from android_mcp.tools.vision import (
    tool_find_element,
    tool_click_element,
)
from android_mcp.tools.tasks import (
    tool_submit_task,
    tool_get_task_status,
    tool_get_task_result,
    tool_cancel_task,
    tool_list_tasks,
    tool_run_task_and_wait,
)

__all__ = [
    # device
    "tool_health_check",
    "tool_get_device_info",
    "tool_get_battery_info",
    "tool_take_screenshot",
    "tool_get_ui_hierarchy",
    # input
    "tool_click",
    "tool_long_click",
    "tool_swipe",
    "tool_drag",
    "tool_type_text",
    "tool_press_key",
    # apps
    "tool_open_app",
    "tool_close_app",
    "tool_clear_app_data",
    "tool_install_app",
    "tool_uninstall_app",
    "tool_get_current_app",
    "tool_list_installed_apps",
    # system
    "tool_shell",
    "tool_get_system_setting",
    "tool_put_system_setting",
    "tool_set_clipboard",
    "tool_get_clipboard",
    "tool_get_notifications",
    "tool_start_activity",
    "tool_get_privilege_mode",
    "tool_set_privilege_mode",
    # files
    "tool_read_file",
    "tool_write_file",
    # vision
    "tool_find_element",
    "tool_click_element",
    # tasks
    "tool_submit_task",
    "tool_get_task_status",
    "tool_get_task_result",
    "tool_cancel_task",
    "tool_list_tasks",
    "tool_run_task_and_wait",
]


def register_all_tools(mcp) -> None:
    """Register all MCP tools on a FastMCP instance.

    Args:
        mcp: FastMCP server instance.
    """

    # -- device --
    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """Check Android device connection status and Shizuku running state."""
        return await tool_health_check()

    @mcp.tool()
    async def get_device_info() -> Dict[str, Any]:
        """Get detailed device info: model, Android version, screen resolution, current app, etc."""
        return await tool_get_device_info()

    @mcp.tool()
    async def get_battery_info() -> Dict[str, Any]:
        """Get battery info: level, charging status, temperature, etc."""
        return await tool_get_battery_info()

    @mcp.tool()
    async def take_screenshot() -> Dict[str, Any]:
        """Capture current screen as a base64-encoded PNG image."""
        return await tool_take_screenshot()

    @mcp.tool()
    async def get_ui_hierarchy() -> Dict[str, Any]:
        """Dump current screen UI hierarchy via uiautomator dump."""
        return await tool_get_ui_hierarchy()

    # -- input --
    @mcp.tool()
    async def click(x: int, y: int) -> Dict[str, Any]:
        """Tap the screen at the given pixel coordinates."""
        return await tool_click(x, y)

    @mcp.tool()
    async def long_click(x: int, y: int, duration: float = 1.0) -> Dict[str, Any]:
        """Long-press the screen at the given pixel coordinates."""
        return await tool_long_click(x, y, duration)

    @mcp.tool()
    async def swipe(
        start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5
    ) -> Dict[str, Any]:
        """Perform a swipe gesture from (start_x,start_y) to (end_x,end_y)."""
        return await tool_swipe(start_x, start_y, end_x, end_y, duration)

    @mcp.tool()
    async def drag(
        start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5
    ) -> Dict[str, Any]:
        """Perform a drag gesture from (start_x,start_y) to (end_x,end_y)."""
        return await tool_drag(start_x, start_y, end_x, end_y, duration)

    @mcp.tool()
    async def type_text(text: str, clear: bool = False) -> Dict[str, Any]:
        """Type text into the currently focused input field."""
        return await tool_type_text(text, clear)

    @mcp.tool()
    async def press_key(key: str) -> Dict[str, Any]:
        """Press a device key (back, home, recent, power, volume_up, volume_down, enter, delete, space, tab, escape, menu, search)."""
        return await tool_press_key(key)

    # -- apps --
    @mcp.tool()
    async def open_app(package_name: str) -> Dict[str, Any]:
        """Launch an app by its package name."""
        return await tool_open_app(package_name)

    @mcp.tool()
    async def close_app(package_name: str) -> Dict[str, Any]:
        """Force-stop an app via am force-stop."""
        return await tool_close_app(package_name)

    @mcp.tool()
    async def clear_app_data(package_name: str, ctx: Context = None) -> Dict[str, Any]:
        """Clear all data for an app via pm clear."""
        allowed, err = await safety.gate(ctx, safety.Risk.HIGH, f"clear app data: {package_name}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_clear_app_data(package_name)

    @mcp.tool()
    async def install_app(apk_path: str, silent: bool = True, ctx: Context = None) -> Dict[str, Any]:
        """Install an APK (supports silent install via Shizuku)."""
        allowed, err = await safety.gate(ctx, safety.Risk.HIGH, f"install APK: {apk_path}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_install_app(apk_path, silent)

    @mcp.tool()
    async def uninstall_app(package_name: str, ctx: Context = None) -> Dict[str, Any]:
        """Uninstall an app by its package name."""
        allowed, err = await safety.gate(ctx, safety.Risk.HIGH, f"uninstall app: {package_name}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_uninstall_app(package_name)

    @mcp.tool()
    async def get_current_app() -> Dict[str, Any]:
        """Get the package name of the currently foreground app."""
        return await tool_get_current_app()

    @mcp.tool()
    async def list_installed_apps() -> Dict[str, Any]:
        """List all installed apps (packages) on the device."""
        return await tool_list_installed_apps()

    # -- system --
    @mcp.tool()
    async def shell(command: str, timeout: float = 30.0, ctx: Context = None) -> Dict[str, Any]:
        """Execute a shell command with ADB/Shizuku/root privileges. High-risk commands require user approval."""
        risk = safety.classify_shell(command)
        allowed, err = await safety.gate(ctx, risk, f"shell command: {command[:200]}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_shell(command, timeout)

    @mcp.tool()
    async def get_system_setting(namespace: str, key: str) -> Dict[str, Any]:
        """Read a system setting (namespace: system, global, secure)."""
        return await tool_get_system_setting(namespace, key)

    @mcp.tool()
    async def put_system_setting(
        namespace: str, key: str, value: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """Write a system setting (requires Shizuku elevated permissions)."""
        risk = safety.Risk.HIGH if namespace.strip().lower() == "secure" else safety.Risk.MEDIUM
        allowed, err = await safety.gate(ctx, risk, f"write system setting: {namespace}.{key}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_put_system_setting(namespace, key, value)

    @mcp.tool()
    async def set_clipboard(text: str) -> Dict[str, Any]:
        """Set the device clipboard content."""
        return await tool_set_clipboard(text)

    @mcp.tool()
    async def get_clipboard() -> Dict[str, Any]:
        """Get the current device clipboard content."""
        return await tool_get_clipboard()

    @mcp.tool()
    async def get_notifications() -> Dict[str, Any]:
        """Get current notifications from the device notification bar."""
        return await tool_get_notifications()

    @mcp.tool()
    async def start_activity(action: str, extra: str = "{}") -> Dict[str, Any]:
        """Start an Activity via an Android Intent."""
        return await tool_start_activity(action, extra)

    @mcp.tool()
    async def get_privilege_mode() -> Dict[str, Any]:
        """Get the active privilege mode/backend on the Android device (auto|shizuku|root)."""
        return await tool_get_privilege_mode()

    @mcp.tool()
    async def set_privilege_mode(mode: str) -> Dict[str, Any]:
        """Set the privilege mode on the Android device: auto, shizuku, or root."""
        return await tool_set_privilege_mode(mode)

    # -- files --
    @mcp.tool()
    async def read_file(path: str) -> Dict[str, Any]:
        """Read a file from the device (supports /data/data and other restricted directories)."""
        return await tool_read_file(path)

    @mcp.tool()
    async def write_file(path: str, content: str, ctx: Context = None) -> Dict[str, Any]:
        """Write content to a file on the device (supports /data/data and other restricted directories)."""
        risk = safety.classify_file_write(path)
        allowed, err = await safety.gate(ctx, risk, f"write file: {path}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_write_file(path, content)

    # -- tasks --
    @mcp.tool()
    async def submit_task(command: str, timeout: float = 0, ctx: Context = None) -> Dict[str, Any]:
        """Submit a command to run in the background on the device. High-risk commands require approval."""
        risk = safety.classify_shell(command)
        allowed, err = await safety.gate(ctx, risk, f"background task command: {command[:200]}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_submit_task(command, timeout)

    @mcp.tool()
    async def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get the current state of a background task (RUNNING/DONE/ERROR/TIMEOUT/CANCELLED)."""
        return await tool_get_task_status(task_id)

    @mcp.tool()
    async def get_task_result(task_id: str) -> Dict[str, Any]:
        """Get the final result (stdout/stderr/exit_code) of a background task."""
        return await tool_get_task_result(task_id)

    @mcp.tool()
    async def cancel_task(task_id: str) -> Dict[str, Any]:
        """Cancel a running background task."""
        return await tool_cancel_task(task_id)

    @mcp.tool()
    async def list_tasks() -> Dict[str, Any]:
        """List all background tasks on the device."""
        return await tool_list_tasks()

    @mcp.tool()
    async def run_task_and_wait(
        command: str,
        timeout: float = 0,
        poll_interval: float = 1.0,
        max_wait: float = 600,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Submit a long-running command and wait for completion (up to max_wait seconds). High-risk commands require approval."""
        risk = safety.classify_shell(command)
        allowed, err = await safety.gate(ctx, risk, f"background task command: {command[:200]}")
        if not allowed:
            return {"success": False, "error": err, "blocked": True}
        return await tool_run_task_and_wait(command, timeout, poll_interval, max_wait)
    # -- vision --
    @mcp.tool()
    async def find_element(description: str) -> Dict[str, Any]:
        """Locate a UI element on screen via vision model — returns coordinates, does not click."""
        return await tool_find_element(description)

    @mcp.tool()
    async def click_element(description: str) -> Dict[str, Any]:
        """Find a UI element via vision model and click it — combines find + click in one step."""
        return await tool_click_element(description)
