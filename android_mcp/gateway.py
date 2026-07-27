"""Android MCP Server — CLI process manager (start/stop/status/restart/forward)."""

import signal
import os
import sys
import subprocess
import time
import argparse

# ========== PID management ==========

PID_DIR = os.path.expanduser("~/.android-mcp")
os.makedirs(PID_DIR, exist_ok=True)


def write_pid(name: str, pid: int) -> None:
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    with open(pid_file, "w") as f:
        f.write(str(pid))


def read_pid(name: str) -> int | None:
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def is_running(name: str) -> bool:
    pid = read_pid(name)
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cleanup_pid(name: str) -> None:
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    try:
        os.remove(pid_file)
    except FileNotFoundError:
        pass


# ========== Colored output ==========

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}{msg}{RESET}")


def err(msg: str) -> None:
    print(f"{RED}{msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}{msg}{RESET}")


def info(msg: str) -> None:
    print(f"{BLUE}{msg}{RESET}")


# ========== Command handlers ==========

WEB_URL = "http://127.0.0.1:8080"


def cmd_start() -> None:
    """Start MCP and Web GUI services."""
    if is_running("mcp"):
        warn("MCP Server is already running")
        return

    if is_running("web"):
        warn("Web GUI is already running")
        return

    mcp_proc = subprocess.Popen(
        [sys.executable, "-m", "android_mcp.main", "--mode", "mcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    write_pid("mcp", mcp_proc.pid)

    web_proc = subprocess.Popen(
        [sys.executable, "-m", "android_mcp.main", "--mode", "web"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    write_pid("web", web_proc.pid)

    ok("Services started")
    info(f"  MCP Server PID: {mcp_proc.pid}")
    info(f"  Web GUI    PID: {web_proc.pid}")
    info(f"  Web GUI   URL: {WEB_URL}")


def _stop_service(name: str) -> None:
    display_name = {"mcp": "MCP Server", "web": "Web GUI"}.get(name, name)

    if not is_running(name):
        warn(f"{display_name} is not running")
        return

    pid = read_pid(name)

    os.kill(pid, signal.SIGTERM)
    info(f"Stopping {display_name} (PID: {pid})...")

    for _ in range(10):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            cleanup_pid(name)
            ok(f"{display_name} stopped")
            return

    os.kill(pid, signal.SIGKILL)
    time.sleep(0.5)
    cleanup_pid(name)
    ok(f"{display_name} force-stopped")


def cmd_stop() -> None:
    """Stop MCP and Web GUI services."""
    _stop_service("mcp")
    _stop_service("web")


def _get_process_runtime(pid: int) -> str:
    """Get process uptime from /proc/{pid}/stat (Linux only)."""
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            stat = f.read()
        close_paren = stat.rfind(")")
        fields = stat[close_paren + 2:].split()
        starttime_ticks = int(fields[19])
        clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        uptime_ticks = time.time() - (starttime_ticks / clk_tck)
        uptime_seconds = int(uptime_ticks)

        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except Exception:
        return "unknown"


def cmd_status() -> None:
    """Show service status."""
    info(f"{BOLD}Android MCP Service Status{RESET}")
    info("-" * 40)

    for name, display_name in [("mcp", "MCP Server"), ("web", "Web GUI")]:
        if is_running(name):
            pid = read_pid(name)
            runtime = _get_process_runtime(pid)
            ok(f"  [ON]  {display_name}: running (PID: {pid}, uptime: {runtime})")
        else:
            err(f"  [OFF] {display_name}: not running")

    info("-" * 40)
    info(f"Web GUI URL: {WEB_URL}")


def cmd_restart() -> None:
    """Restart services."""
    cmd_stop()
    time.sleep(1)
    cmd_start()


def cmd_forward() -> None:
    """Set up ADB port forwarding."""
    try:
        subprocess.run(
            ["adb", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        err("adb not available. Install Android SDK Platform Tools and add to PATH.")
        return

    result = subprocess.run(
        ["adb", "forward", "tcp:18080", "tcp:18080"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        if result.stdout.strip():
            info(result.stdout.strip())
        ok("ADB port forward: tcp:18080 -> tcp:18080")
    else:
        err(f"ADB port forward failed: {result.stderr.strip()}")


# ========== CLI ==========


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="android-mcp-gateway",
        description="Android MCP Server management tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("start", help="Start MCP and Web GUI services")
    subparsers.add_parser("stop", help="Stop MCP and Web GUI services")
    subparsers.add_parser("status", help="Show service status")
    subparsers.add_parser("restart", help="Restart services")
    subparsers.add_parser(
        "forward", help="Set up ADB port forward (tcp:18080 -> tcp:18080)"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    handlers = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "restart": cmd_restart,
        "forward": cmd_forward,
    }

    handlers[args.command]()


if __name__ == "__main__":
    main()
