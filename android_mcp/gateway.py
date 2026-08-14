"""Android MCP Server — CLI process manager (start/stop/status/restart/forward)."""

import signal
import os
import sys
import subprocess
import time
import argparse

from android_mcp.config import config
from android_mcp.console import (
    BLUE,
    BOLD,
    GREEN,
    RED,
    RESET,
    YELLOW,
    err,
    info,
    ok,
    setup_utf8,
    warn,
)

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


def _pid_exists(pid: int) -> bool:
    """Check whether a PID is alive, cross-platform.

    os.kill(pid, 0) is NOT a reliable liveness check on Windows: signal 0 maps
    to GenerateConsoleCtrlEvent(CTRL_C_EVENT, pid), which raises WinError 87 for
    any pid outside the current console group — dead or alive. Use psutil when
    available, falling back to OpenProcess on Windows and os.kill(0) on POSIX.
    """
    try:
        import psutil
    except ImportError:
        psutil = None

    if psutil is not None:
        return psutil.pid_exists(pid)

    if os.name == "nt":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False

    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True  # process exists but isn't ours to signal
    except (ProcessLookupError, OSError):
        return False


def _port_in_use(port: int) -> bool:
    """Return True if something is listening on the given TCP port."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


# Service registry: name -> {display, port, mode}.
SERVICES = {
    "mcp": {"display": "MCP Server", "port": config.MCP_PORT, "mode": "mcp-sse"},
    "web": {"display": "Web GUI", "port": config.WEB_PORT, "mode": "web"},
}


def is_running(name: str) -> bool:
    """True if the service is alive — by PID or by its listening port.

    The port check is the single-instance guard: even if the PID file is stale
    (crashed process left the file, or the PID was reused), a bound port means a
    real instance is still serving and must not be duplicated.
    """
    pid = read_pid(name)
    if pid is not None and _pid_exists(pid):
        return True
    return _port_in_use(SERVICES[name]["port"])


def cleanup_pid(name: str) -> None:
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    try:
        os.remove(pid_file)
    except FileNotFoundError:
        pass


# ========== Command handlers ==========

WEB_URL = f"http://127.0.0.1:{config.WEB_PORT}"


def _show_log(title: str, path: str) -> None:
    """Print the current tail of a service log file (or a placeholder)."""
    info(f"{BOLD}── {title} ──{RESET}")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        text = ""
    if text.strip():
        print(text, end=("" if text.endswith("\n") else "\n"))
    else:
        info("  (no output yet)")


def _start_service(name: str) -> int:
    """Launch one service process (logging to a file), return its PID."""
    spec = SERVICES[name]
    log_path = os.path.join(PID_DIR, f"{name}.log")

    # --mode mcp is stdio-only (no listening port) and dies immediately when
    # detached, so MCP uses mcp-sse. -u keeps output unbuffered so startup logs
    # reach the file before the tail below runs.
    log = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "android_mcp.main", "--mode", spec["mode"]],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    log.close()  # parent no longer needs the handle; the child keeps its own
    write_pid(name, proc.pid)
    return proc.pid


def cmd_start() -> None:
    """Start MCP and Web GUI services, skipping any that are already running."""
    started = False
    for name in ("mcp", "web"):
        display = SERVICES[name]["display"]
        if is_running(name):
            warn(f"{display} is already running")
            continue
        pid = _start_service(name)
        info(f"  {display} PID: {pid} (port {SERVICES[name]['port']})")
        started = True

    if not started:
        return

    mcp_log_path = os.path.join(PID_DIR, "mcp.log")
    web_log_path = os.path.join(PID_DIR, "web.log")
    ok("Services started")
    info(f"  Web GUI   URL: {WEB_URL}")
    info(f"  Logs: {mcp_log_path} / {web_log_path}")
    info(f"  Follow: python -m android_mcp.gateway logs")

    # Surface the startup output so it's visible immediately.
    time.sleep(2)
    _show_log("MCP Server", mcp_log_path)
    _show_log("Web GUI", web_log_path)


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
        if not _pid_exists(pid):
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
    """Get process uptime, cross-platform (Linux /proc, Windows psutil)."""
    # Try Linux /proc first
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            stat = f.read()
        close_paren = stat.rfind(")")
        fields = stat[close_paren + 2:].split()
        starttime_ticks = int(fields[19])
        clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        uptime_seconds = int(time.time() - (starttime_ticks / clk_tck))
    except Exception:
        # Fallback: use psutil if available, otherwise return "unknown"
        try:
            import psutil
            proc = psutil.Process(pid)
            uptime_seconds = int(time.time() - proc.create_time())
        except Exception:
            return "unknown"

    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


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


def cmd_logs() -> None:
    """Tail MCP and Web GUI logs in real time (Ctrl+C to stop)."""
    logs = [
        ("MCP Server", os.path.join(PID_DIR, "mcp.log")),
        ("Web GUI", os.path.join(PID_DIR, "web.log")),
    ]

    # Show only the tail of existing output (not the whole file), then follow
    # new appends. Prevents an idle service's history from flooding the terminal
    # and then going silent, which read as "the command quit".
    tail_lines = 30
    offsets: dict[str, int] = {}
    for name, path in logs:
        info(f"{BOLD}── {name} ({path}) ──{RESET}")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            if lines:
                start = max(0, len(lines) - tail_lines)
                chunk = "".join(lines[start:])
                print(chunk, end=("" if chunk.endswith("\n") else "\n"), flush=True)
            else:
                info("  (log is empty)")
            # Position after the whole file so we only follow *new* appends.
            offsets[path] = os.path.getsize(path)
        except FileNotFoundError:
            info("  (no log yet — run 'start' first)")
            offsets[path] = 0

    info(f"{BOLD}── following new output (Ctrl+C to stop) ──{RESET}")
    try:
        while True:
            time.sleep(1)
            for _, path in logs:
                try:
                    size = os.path.getsize(path)
                except FileNotFoundError:
                    continue
                start = offsets.get(path, 0)
                if size < start:  # file was truncated/rotated
                    start = 0
                if size > start:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(start)
                        print(f.read(), end="", flush=True)
                    offsets[path] = size
    except KeyboardInterrupt:
        print()
        info("Stopped following logs.")


# ========== CLI ==========


def main() -> None:
    setup_utf8()
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
    subparsers.add_parser("logs", help="Tail MCP and Web GUI logs in real time")

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
        "logs": cmd_logs,
    }

    handlers[args.command]()


if __name__ == "__main__":
    main()
