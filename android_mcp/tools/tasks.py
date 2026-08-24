"""Tools: long-running task automation (submit / poll / cancel / result)."""

import asyncio
import time
from typing import Any, Dict

from android_mcp import bridge
from android_mcp.tools.decorators import bridge_call


@bridge_call
async def tool_submit_task(command: str, timeout: float = 0) -> Dict[str, Any]:
    """Submit a command to run in the background on the device. Returns task_id."""
    return await bridge.submit_task(command, timeout)


@bridge_call
async def tool_get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the current state of a background task (RUNNING/DONE/ERROR/TIMEOUT/CANCELLED)."""
    return await bridge.get_task_status(task_id)


@bridge_call
async def tool_get_task_result(task_id: str) -> Dict[str, Any]:
    """Get the final result (stdout/stderr/exit_code) of a background task."""
    return await bridge.get_task_result(task_id)


@bridge_call
async def tool_cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a running background task."""
    return await bridge.cancel_task(task_id)


@bridge_call
async def tool_list_tasks() -> Dict[str, Any]:
    """List all background tasks on the device."""
    return await bridge.list_tasks()


async def tool_run_task_and_wait(
    command: str,
    timeout: float = 0,
    poll_interval: float = 1.0,
    max_wait: float = 600,
) -> Dict[str, Any]:
    """Submit a task and poll until it finishes — one call runs a long command.

    ``timeout`` and ``max_wait`` are in seconds (<= 0 timeout = unlimited).
    Returns the final task result once the command reaches DONE/ERROR/TIMEOUT/CANCELLED,
    or an error if ``max_wait`` elapses while still RUNNING.
    """
    try:
        submitted = await bridge.submit_task(command, timeout)
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not submitted.get("success"):
        return {"success": False, "error": submitted.get("error", "submit failed")}

    tid = submitted.get("task_id", "")
    if not tid:
        return {"success": False, "error": "submit returned no task_id"}

    deadline = time.time() + max_wait
    while time.time() < deadline:
        st = await bridge.get_task_status(tid)
        if st.get("state") in ("DONE", "ERROR", "TIMEOUT", "CANCELLED"):
            return await bridge.get_task_result(tid)
        await asyncio.sleep(max(0.05, poll_interval))

    return {
        "success": False,
        "task_id": tid,
        "error": "max_wait exceeded, task still RUNNING",
    }