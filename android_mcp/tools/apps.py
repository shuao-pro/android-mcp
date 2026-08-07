"""Tools: app management (open, close, install, uninstall, list, etc.)."""

from typing import Dict, Any

from android_mcp import bridge
from android_mcp.tools.decorators import bridge_call


@bridge_call
async def tool_open_app(package_name: str) -> Dict[str, Any]:
    return await bridge.open_app(package_name)


@bridge_call
async def tool_close_app(package_name: str) -> Dict[str, Any]:
    return await bridge.close_app(package_name)


@bridge_call
async def tool_clear_app_data(package_name: str) -> Dict[str, Any]:
    return await bridge.clear_app_data(package_name)


@bridge_call
async def tool_install_app(apk_path: str, silent: bool = True) -> Dict[str, Any]:
    """Silent install APK via Shizuku (requires APK path on device)."""
    return await bridge.install_app(apk_path, silent)


@bridge_call
async def tool_uninstall_app(package_name: str) -> Dict[str, Any]:
    return await bridge.uninstall_app(package_name)


@bridge_call
async def tool_get_current_app() -> Dict[str, Any]:
    return await bridge.get_current_app()


@bridge_call
async def tool_list_installed_apps() -> Dict[str, Any]:
    return await bridge.list_installed_apps()
