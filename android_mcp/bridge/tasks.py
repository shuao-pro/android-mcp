"""Bridge: long-running command tasks (submit → poll → result)."""

from typing import Any

from android_mcp.bridge._core import _send


async def submit_task(command: str, timeout: float = 0) -> dict[str, Any]:
    """Submit a command to run in the background on the device.

    ``timeout`` is in seconds; <= 0 means unlimited. Returns ``task_id``.
    """
    timeout_ms = int(timeout * 1000) if timeout and timeout > 0 else 0
    return await _send("task.submit", {"command": command, "timeout": timeout_ms})


async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get the current state of a background task (instant)."""
    return await _send("task.status", {"task_id": task_id})


async def get_task_result(task_id: str) -> dict[str, Any]:
    """Get the final result (stdout/stderr/exit code) of a background task."""
    return await _send("task.result", {"task_id": task_id})


async def cancel_task(task_id: str) -> dict[str, Any]:
    """Cancel a running background task."""
    return await _send("task.cancel", {"task_id": task_id})


async def list_tasks() -> dict[str, Any]:
    """List all background tasks on the device."""
    return await _send("task.list")