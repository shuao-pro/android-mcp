"""Tools: file system access (read/write files on device via Shizuku)."""

from typing import Dict, Any

from android_mcp import bridge


async def tool_read_file(path: str) -> Dict[str, Any]:
    """Read file from device (supports /data/data restricted dirs)."""
    try:
        return await bridge.read_file(path)
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_write_file(path: str, content: str) -> Dict[str, Any]:
    """Write file to device (supports /data/data restricted dirs)."""
    try:
        return await bridge.write_file(path, content)
    except Exception as e:
        return {"success": False, "error": str(e)}
