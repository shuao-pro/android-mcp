"""Android MCP Bridge — JSON-RPC transport to Android device via Shizuku + ADB.

Split into domain modules for maintainability. Import from android_mcp.bridge
directly to access all bridge functions.
"""

from android_mcp.bridge._core import (
    _send,
    _adb,
    _adb_bytes,
    _ensure_adb_forward,
    _to_millis,
    get_history,
)
from android_mcp.bridge.device import (
    fast_screenshot,
    get_device_info,
    get_screenshot,
    get_ui_hierarchy,
    health_check,
    reboot,
    screen_off,
    screen_on,
    shell,
)
from android_mcp.bridge.input import (
    click,
    drag,
    long_click,
    press_key,
    press_keycode,
    swipe,
    type_text,
)
from android_mcp.bridge.apps import (
    clear_app_data,
    close_app,
    get_current_app,
    install_app,
    list_installed_apps,
    open_app,
    uninstall_app,
)
from android_mcp.bridge.files import (
    delete_file,
    file_stat,
    list_files,
    read_file,
    write_file,
)
from android_mcp.bridge.tasks import (
    cancel_task,
    get_task_result,
    get_task_status,
    list_tasks,
    submit_task,
)
from android_mcp.bridge.system import (
    cancel_notification,
    get_battery_info,
    get_clipboard,
    get_mode,
    get_notifications,
    get_system_setting,
    put_system_setting,
    set_clipboard,
    set_mode,
    start_activity,
)

__all__ = [
    # core
    "get_history",
    # device
    "health_check",
    "get_device_info",
    "get_screenshot",
    "fast_screenshot",
    "shell",
    "get_ui_hierarchy",
    "reboot",
    "screen_on",
    "screen_off",
    # input
    "click",
    "long_click",
    "swipe",
    "drag",
    "type_text",
    "press_key",
    "press_keycode",
    # apps
    "open_app",
    "close_app",
    "clear_app_data",
    "install_app",
    "uninstall_app",
    "list_installed_apps",
    "get_current_app",
    # files
    "read_file",
    "write_file",
    "list_files",
    "file_stat",
    "delete_file",
    # system
    "get_system_setting",
    "put_system_setting",
    "get_battery_info",
    "set_clipboard",
    "get_clipboard",
    "get_notifications",
    "cancel_notification",
    "start_activity",
    "get_mode",
    "set_mode",
    # tasks
    "submit_task",
    "get_task_status",
    "get_task_result",
    "cancel_task",
    "list_tasks",
]
