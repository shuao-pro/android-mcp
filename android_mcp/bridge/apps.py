"""Bridge: app management (open, close, install, uninstall, list)."""

from typing import Any

from android_mcp.bridge._core import _send
from android_mcp.bridge.device import shell


async def open_app(package_name: str, activity: str = "") -> dict[str, Any]:
    """Launch an app by package name."""
    return await _send("package.open", {
        "package": package_name, "activity": activity,
    })


async def close_app(package_name: str) -> dict[str, Any]:
    """Force-stop an app."""
    return await _send("package.close", {"package": package_name})


async def clear_app_data(package_name: str) -> dict[str, Any]:
    """Clear all data for an app."""
    return await _send("package.clear_data", {"package": package_name})


async def install_app(
    apk_path: str, silent: bool = True, allow_downgrade: bool = False,
) -> dict[str, Any]:
    """Install an APK via Shizuku."""
    return await _send("package.install", {
        "apk_path": apk_path,
        "silent": silent,
        "allow_downgrade": allow_downgrade,
    })


async def uninstall_app(package_name: str, keep_data: bool = False) -> dict[str, Any]:
    """Uninstall an app."""
    return await _send("package.uninstall", {
        "package": package_name, "keep_data": keep_data,
    })


async def list_installed_apps(
    filter: str = "", include_system: bool = False,
) -> dict[str, Any]:
    """List installed apps, optionally filtered."""
    return await _send("package.list", {
        "filter": filter, "include_system": include_system,
    })


async def get_current_app() -> dict[str, Any]:
    """Get the package name of the foreground app."""
    return await shell(
        "dumpsys window | grep mCurrentFocus | awk '{print $3}' | cut -d/ -f1"
    )
