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

        resp = httpx.get(
            f"{config.ANDROID_BASE_URL}/health",
            timeout=3.0,
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
    from android_mcp.utils import get_lan_ip

    host, port = config.WEB_HOST, config.WEB_PORT
    mcp_host, mcp_port = config.MCP_HOST, config.MCP_PORT
    lan_ip = get_lan_ip()

    print("=" * 60)
    print("  Android MCP Server v2.0.2")
    print("  Shizuku + ADB Tunnel")
    print("=" * 60)

    if mode in ("mcp-sse", "all-sse"):
        print(f"  MCP:       http://{mcp_host}:{mcp_port}/sse  (SSE)")
        print(f"             http://{mcp_host}:{mcp_port}/mcp  (Streamable HTTP)")
        if mcp_host in ("0.0.0.0", ""):
            print(f"             http://{lan_ip}:{mcp_port}/sse  (LAN)")
            print(f"             http://{lan_ip}:{mcp_port}/mcp  (LAN)")
        if mcp_host == "127.0.0.1":
            print("  [!] MCP_HOST=127.0.0.1 — phone/WiFi clients WON'T reach this!")
            print("     Set MCP_HOST=0.0.0.0 in .env to allow external connections.")
        print()
        print("  Kai 9000 → use the /mcp endpoint")
        print("  Claude Desktop → use the /sse endpoint")
    if mode in ("mcp-http",):
        print(f"  MCP HTTP:  http://{mcp_host}:{mcp_port}/mcp")
    if mode in ("mcp", "all"):
        print("  MCP:       stdio (local)")
    if mode in ("web", "all", "all-sse"):
        print(f"  Web GUI:   http://{host}:{port}")
    print("-" * 60)

    if mode != "web":
        print("  Checking Android device...", end=" ", flush=True)
        if check_android_connectivity():
            print("CONNECTED")
        else:
            print("NOT FOUND")
            print("-" * 60)
            print("  WARNING: Android device not reachable at")
            print(f"  {config.ANDROID_BASE_URL}")
            print()
            print("  To fix:")
            print(f"  1. Start Shizuku on your phone")
            print(f"  2. Open Android MCP app → tap Start")
            print(f"  3. Run: adb forward tcp:{config.ANDROID_PORT} tcp:{config.ANDROID_PORT}")
    else:
        print()

    if sys.platform == "win32" and mcp_host in ("0.0.0.0", lan_ip):
        print(f"  💡 Windows Firewall may block port {mcp_port}. Allow Python on first prompt.")

    print("=" * 60)


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
        print(f"  Connect your MCP client to: http://{mcp_host}:{mcp_port}/sse")
        from android_mcp.server import run_mcp_combined
        asyncio.run(run_mcp_combined(mcp_host, mcp_port))

    elif mode == "mcp-http":
        print(f"  Connect your MCP client to: http://{mcp_host}:{mcp_port}/mcp")
        from android_mcp.server import run_mcp_streamable_http
        asyncio.run(run_mcp_streamable_http(mcp_host, mcp_port))

    elif mode == "web":
        start_web_gui()

    elif mode == "mcp":
        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    run()
