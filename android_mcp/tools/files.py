"""Tools: file system access (read/write files on device via Shizuku)."""

from typing import Dict, Any

from android_mcp import bridge
from android_mcp.tools.decorators import bridge_call


@bridge_call
async def tool_read_file(path: str) -> Dict[str, Any]:
    """Read file from device (supports /data/data restricted dirs)."""
    return await bridge.read_file(path)


@bridge_call
async def tool_write_file(path: str, content: str) -> Dict[str, Any]:
    """Write file to device (supports /data/data restricted dirs)."""
    return await bridge.write_file(path, content)
