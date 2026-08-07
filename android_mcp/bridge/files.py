"""Bridge: file system access on device via Shizuku."""

from typing import Any

from android_mcp.bridge._core import _send


async def read_file(path: str) -> dict[str, Any]:
    """Read a file from the device."""
    return await _send("file.read", {"path": path})


async def write_file(path: str, content: str, append: bool = False) -> dict[str, Any]:
    """Write content to a file on the device."""
    return await _send("file.write", {
        "path": path, "content": content, "append": append,
    })


async def list_files(path: str = "/sdcard") -> dict[str, Any]:
    """List files in a directory on the device."""
    return await _send("file.list", {"path": path})


async def file_stat(path: str) -> dict[str, Any]:
    """Get file metadata (size, permissions, timestamps)."""
    return await _send("file.stat", {"path": path})


async def delete_file(path: str, recursive: bool = False) -> dict[str, Any]:
    """Delete a file or directory on the device."""
    return await _send("file.delete", {"path": path, "recursive": recursive})
