"""Entry point for Android MCP Server.

Usage:
    python -m android_mcp.main                  # all-sse (SSE+Streamable HTTP+Web GUI, default)
    python -m android_mcp.main --mode mcp       # MCP stdio only
    python -m android_mcp.main --mode mcp-sse   # SSE + Streamable HTTP (headless)
    python -m android_mcp.main --mode mcp-http  # Streamable HTTP only
    python -m android_mcp.main --mode web       # Web GUI only
    python -m android_mcp.main --mode all       # MCP stdio + Web GUI
    python -m android_mcp.main --mode all-sse   # SSE + Streamable HTTP + Web GUI
"""

import asyncio
import sys
import threading


def check_android_connectivity() -> bool:
    """Quick check if Android device is reachable. Returns True if connected."""
    import httpx

    try:
        from android_mcp.config import config

        headers = {"X-MCP-Token": config.ANDROID_TOKEN} if config.ANDROID_TOKEN else {}
        resp = httpx.get(
            f"{config.ANDROID_BASE_URL}/health",
            timeout=3.0,
            headers=headers,
        )
        data = resp.json()
        if data.get("result") == "ok" or data.get("connected"):
            return True
    except Exception:
        pass
    return False


def print_startup_banner(mode: str) -> None:
    """Print server startup banner with connectivity status."""
    from android_mcp.config import config
    from android_mcp.console import BOLD, DIM, RESET, err, ok, paint, warn
    from android_mcp.utils import get_lan_ip, get_version

    host, port = config.WEB_HOST, config.WEB_PORT
    mcp_host, mcp_port = config.MCP_HOST, config.MCP_PORT
    lan_ip = get_lan_ip()

    bar = paint("=" * 60, DIM)
    print(bar)
    print(f"  {paint('Android MCP Server', BOLD)} {paint('v' + get_version(), DIM)}")
    print(f"  {paint('Shizuku + ADB Tunnel', DIM)}")
    print(bar)

    if mode in ("mcp-sse", "all-sse"):
        print(f"  MCP:       http://{mcp_host}:{mcp_port}/sse  (SSE)")
        print(f"             http://{mcp_host}:{mcp_port}/mcp  (Streamable HTTP)")
        if mcp_host in ("0.0.0.0", ""):
            print(f"             http://{lan_ip}:{mcp_port}/sse  (LAN)")
            print(f"             http://{lan_ip}:{mcp_port}/mcp  (LAN)")
        if mcp_host == "127.0.0.1":
            warn("  [!] MCP_HOST=127.0.0.1 — phone/WiFi clients WON'T reach this!")
            warn("      Set MCP_HOST=0.0.0.0 in .env to allow external connections.")
        print()
        print(f"  {paint('Kai 9000', BOLD)} → /mcp endpoint")
        print(f"  {paint('Claude Desktop', BOLD)} → /sse endpoint")
    if mode in ("mcp-http",):
        print(f"  MCP HTTP:  http://{mcp_host}:{mcp_port}/mcp")
    if mode in ("mcp", "all"):
        print("  MCP:       stdio (local)")
    if mode in ("web", "all", "all-sse"):
        print(f"  Web GUI:   http://{host}:{port}")
    print(paint("-" * 60, DIM))

    if mode != "web":
        print("  Checking Android device...", end=" ", flush=True)
        if check_android_connectivity():
            ok("CONNECTED")
        else:
            err("NOT FOUND")
            print(paint("-" * 60, DIM))
            warn("  Android device not reachable at")
            print(f"  {config.ANDROID_BASE_URL}")
            print()
            print("  To fix:")
            print("  1. Start Shizuku on your phone")
            print("  2. Open Android MCP app → tap Start")
            print("  3. Copy the token shown in the app into .env → ANDROID_TOKEN=")
            print(f"  4. Run: adb forward tcp:{config.ANDROID_PORT} tcp:{config.ANDROID_PORT}")
    else:
        print()

    if sys.platform == "win32" and mcp_host in ("0.0.0.0", lan_ip):
        warn(f"  [!] Windows Firewall may block port {mcp_port}. Allow Python on first prompt.")

    print(bar)


def start_web_gui():
    """Start Web GUI in a daemon thread."""
    import uvicorn
    from contextlib import asynccontextmanager
    from android_mcp.web.server import app, mount_static, broadcast_status
    from android_mcp.config import config

    mount_static()

    @asynccontextmanager
    async def lifespan(application):
        task = asyncio.create_task(broadcast_status())
        yield
        task.cancel()

    app.router.lifespan_context = lifespan
    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT, log_level="info")


def parse_args():
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Android MCP Server")
    parser.add_argument(
        "--mode",
        choices=["mcp", "mcp-sse", "mcp-http", "web", "all", "all-sse"],
        default="all-sse",
        help=(
            "Startup mode: mcp (stdio), mcp-sse (SSE + Streamable HTTP), "
            "mcp-http (Streamable HTTP only), web (GUI only), all (stdio+GUI), "
            "all-sse (SSE + Streamable HTTP + GUI, default)"
        ),
    )
    return parser.parse_args()


def run(mode: str | None = None) -> None:
    """Main entry point. Accepts mode string or parses CLI args if None.

    Args:
        mode: One of 'mcp', 'mcp-sse', 'mcp-http', 'web', 'all', 'all-sse'.
              If None, parsed from sys.argv.
    """
    from android_mcp.server import mcp, setup
    from android_mcp.config import config
    from android_mcp.console import setup_utf8

    setup_utf8()
    setup()

    if mode is None:
        args = parse_args()
        mode = args.mode

    host, port = config.WEB_HOST, config.WEB_PORT
    mcp_host, mcp_port = config.MCP_HOST, config.MCP_PORT

    print_startup_banner(mode)

    if mode == "all-sse":
        web_thread = threading.Thread(target=start_web_gui, daemon=True)
        web_thread.start()
        from android_mcp.server import run_mcp_combined
        asyncio.run(run_mcp_combined(mcp_host, mcp_port))

    elif mode == "all":
        web_thread = threading.Thread(target=start_web_gui, daemon=True)
        web_thread.start()
        asyncio.run(mcp.run_stdio_async())

    elif mode == "mcp-sse":
        from android_mcp.server import run_mcp_combined
        asyncio.run(run_mcp_combined(mcp_host, mcp_port))

    elif mode == "mcp-http":
        from android_mcp.server import run_mcp_streamable_http
        asyncio.run(run_mcp_streamable_http(mcp_host, mcp_port))

    elif mode == "web":
        start_web_gui()

    elif mode == "mcp":
        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    run()
