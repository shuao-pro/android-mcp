"""FastMCP server definition for Android MCP Server.

Supports three transport modes:
- stdio:  local process communication (Claude Desktop, etc.)
- sse:    HTTP SSE transport (web frontends, remote MCP clients)
- streamable-http: new MCP streamable HTTP transport
- combined: SSE + Streamable HTTP on the same port (for Kai 9000, etc.)
"""

from mcp.server.fastmcp import FastMCP

# DNS rebinding protection is left enabled (the MCP default): it rejects
# requests whose Host header is not localhost. This is safe now that
# MCP_HOST defaults to 127.0.0.1. If you explicitly set MCP_HOST=0.0.0.0 to
# serve LAN clients (e.g. Kai 9000 on a phone), configure allowed hosts or
# disable this protection via transport_security.

mcp = FastMCP(
    name="Android MCP Server",
    instructions=(
        "MCP Server for Android device automation via Shizuku + ADB tunnel. "
        "Provides system-level control over Android devices including: shell commands, "
        "UI input injection, app management (install/uninstall/clear), file system access, "
        "system settings read/write, clipboard, notifications, and more. "
        "All through Shizuku's elevated permissions (UID 2000)."
    ),
)


def setup() -> None:
    """Register all tools and finalize server setup."""
    from android_mcp.tools import register_all_tools

    register_all_tools(mcp)


async def run_mcp_stdio():
    """Start MCP via stdio (local process communication)."""
    await mcp.run_stdio_async()


def _make_combined_app():
    """Build an ASGI app that dispatches SSE and Streamable HTTP on one port.

    Routes /mcp* to the Streamable HTTP transport,
    everything else to the SSE transport.

    Properly runs the streamable HTTP app's lifespan to initialize its
    session manager (required for Kai 9000 / other MCP clients).
    """
    from starlette.responses import JSONResponse

    sse = mcp.sse_app()
    streamable = mcp.streamable_http_app()

    # Raw ASGI dispatch — sub-apps write directly to send(), can't use
    # Starlette Route which expects a Response return value.
    async def combined_asgi(scope, receive, send):
        if scope["type"] == "lifespan":
            # Delegate lifespan to the streamable app (it needs task group init).
            # The SSE app doesn't rely on a custom lifespan.
            await streamable(scope, receive, send)
            return

        path = scope.get("path", "/")
        if path == "/health":
            response = JSONResponse({"status": "ok", "transports": ["sse", "streamable-http"]})
            await response(scope, receive, send)
        elif path.startswith("/mcp"):
            await streamable(scope, receive, send)
        else:
            await sse(scope, receive, send)

    return combined_asgi


async def run_mcp_sse(host: str = "127.0.0.1", port: int = 9000):
    """Start MCP via SSE over HTTP (for web frontends and remote clients).

    Exposes:
        http://{host}:{port}/sse       - SSE event stream
        http://{host}:{port}/messages  - client message endpoint

    MCP clients connect to: http://{host}:{port}/sse
    """
    import uvicorn

    app = mcp.sse_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_mcp_streamable_http(host: str = "127.0.0.1", port: int = 9000):
    """Start MCP via Streamable HTTP (new MCP transport).

    Exposes:
        http://{host}:{port}/mcp  - streamable HTTP endpoint
    """
    import uvicorn

    app = mcp.streamable_http_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_mcp_combined(host: str = "0.0.0.0", port: int = 9000):
    """Start both SSE and Streamable HTTP on the same port.

    Exposes:
        http://{host}:{port}/sse       - SSE event stream (GET)
        http://{host}:{port}/messages  - SSE client messages (POST)
        http://{host}:{port}/mcp       - Streamable HTTP endpoint (POST/GET/DELETE)

    Kai 9000 uses Streamable HTTP → connect to http://{host}:{port}/mcp
    """
    import uvicorn

    app = _make_combined_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
