# Development Log — Android MCP Server

## v2.0.2 (2026-07-14)

### MCP Transport — Dual SSE + Streamable HTTP on One Port

- **Combined transport (`server.py`)** — new `_make_combined_app()` raw ASGI dispatcher routes `/mcp*` to Streamable HTTP and everything else to SSE on the same port. Enables Kai 9000 (Streamable HTTP) and Claude Desktop (SSE) to connect simultaneously.
- **Fixed Streamable HTTP 500** — the `streamable_http_app()` requires Starlette lifespan to initialize its session manager task group. Previous Route-based dispatch bypassed lifespan; now uses raw ASGI with proper lifespan delegation.
- **Fixed transport security 421** — `TransportSecuritySettings` only supports exact host matching and `:*` port wildcards, NOT IP-octet wildcards (`192.168.*.*`). Disabled DNS rebinding protection since this is a local-network tool. Kai 9000 from phone WiFi can now connect without `421 Misdirected Request`.
- **`MCP_HOST` default changed to `0.0.0.0`** — was `127.0.0.1` which only accepted local connections. Phones on the same WiFi couldn't reach the server. Also updated `.env` and `.env.example`.
- **New `run_mcp_combined()`** — single function to start both transports for `all-sse` and `mcp-sse` modes.

### Bridge Resilience

- **`bridge._send()` error handling** — previously crashed the entire WebSocket connection when Android device was unreachable. Now catches 5 exception types (`ConnectError`, `RemoteProtocolError`, `TimeoutException`, `HTTPStatusError`, generic `Exception`) and returns structured `{success: False, error: "..."}` dicts. All 29 MCP tools now return friendly errors instead of crashing.

### WebSocket Stability

- **`ws_endpoint` three-layer protection** — JSON parse errors return error messages instead of disconnecting; all bridge commands wrapped in try-catch; `send_text` failures gracefully exit the loop.
- **`finally` block cleanup** — `_ws_clients.discard(ws)` always runs, preventing client set leaks.
- **`broadcast_status()` global declaration** — already fixed in v2.0.1, verified working.

### Startup Diagnostics

- **Android connectivity check at startup** — `check_android_connectivity()` probes `ANDROID_BASE_URL/health` (3s timeout) before server starts. Prints clear WARNING with numbered fix steps when device is unreachable.
- **`print_startup_banner()`** — unified banner shows all endpoints (SSE + Streamable HTTP), LAN IP, Kai 9000 / Claude Desktop usage hints, and Windows Firewall reminder.
- **LAN IP auto-detection** — UDP socket trick to find the actual LAN IP for display.

### Web GUI Improvements

- **Fixed duplicate DOM elements** — removed orphaned `</div>` and duplicate `#deviceModel` in header.
- **MCP client count in header** — shows "1 MCP" (blue) when Kai 9000 or other clients are connected.
- **Setup Wizard shows both endpoints** — displays `/sse` (SSE label) and `/mcp` (HTTP label) with LAN variants. Kai 9000 users see the correct `/mcp` endpoint.
- **Better error feedback** — `formatToolResult()` detects bridge errors ("not reachable", "disconnected") and shows a fix guide inline in chat.
- **Markdown improvements** — link rendering (`[text](url)`), table support, skeleton loading animation CSS.
- **CSS refinements** — streaming green border on screenshot frame, `.btn.small` variant, disabled button state, responsive breakpoint polish, consolidated duplicate `.shell-output` rule.

### Configuration

- **`transport_security` on FastMCP** — `enable_dns_rebinding_protection=False` for LAN accessibility.
- **`MCP_HOST=0.0.0.0`** — default now accepts all interfaces (was `127.0.0.1`).

---

## v2.0.1 (2026-07-14)

### Android APK Crash Fixes

- **Fixed `WifiManager` crash on Android 14+** — replaced `WifiManager.getConnectionInfo()` (hard-deprecated at SDK 35) with `ConnectivityManager` + `NetworkCapabilities` + `LinkProperties`. This was the primary cause of instant crash on modern devices.
- **Fixed Shizuku API unsafe calls** — extracted safe wrappers (`tryPingShizuku()`, `tryCheckPermission()`, `tryRequestPermission()`, `tryStartService()`) with try-catch guards. Prevents crash when Shizuku is in a bad state.
- **Fixed `startForegroundService` crash** — wrapped in try-catch for Chinese ROMs (OPPO/Xiaomi) that reject `specialUse` foreground services.
- **Fixed `typeText` pipe approach** — replaced `echo | base64 -d | input text` (broken on many ROMs) with temp-file + `input text "$(cat ...)"` argument mode.
- **Fixed Shell stdout/stderr deadlock** — concurrent `thread {}` reading of stdout and stderr to prevent pipe-buffer deadlock.
- **Fixed Shizuku listener leak** — stored listener lambdas as fields; proper cleanup in `onDestroy()` via `removeBinderReceivedListener` / `removeBinderDeadListener`.
- **Added `ACCESS_NETWORK_STATE` permission** (replaces `ACCESS_WIFI_STATE`).
- **Added `PROPERTY_SPECIAL_USE_FGS_SUBTYPE`** on `<service>` — required by Android 14+.

### Server Bug Fixes

- **Fixed `_ws_clients` `UnboundLocalError`** — `broadcast_status()` augmented assignment (`_ws_clients -= dead`) made Python treat the module-level set as a local variable. Added `global _ws_clients` declaration.
- **Fixed `on_event` deprecation** — replaced `@app.on_event("startup")` with `asynccontextmanager` lifespan handler.
- **Fixed MCP SSE on wrong port (8000 vs 9000)** — `main.py` was calling FastMCP's built-in `run_sse_async()` instead of the project's `run_mcp_sse()`, ignoring `MCP_PORT` config.

### MCP Tool Docstrings — Chinese → English

- All 29 tool docstrings in `tools/__init__.py` translated from Chinese to English for better LLM tool-calling accuracy with MCP clients like Kai 9000.
- Moved `shell` tool registration from `# -- apps --` to `# -- system --` (was in the wrong section).

### Setup Wizard — MCP Frontend + Server Address

- Step 3 changed from "Start Android MCP App" to "Launch MCP API Frontend" — guides users to install Kai 9000 (F-Droid) or any MCP client.
- `/api/setup/status` now returns `server_address`, `server_local`, `server_ip` — auto-detects LAN IP via UDP socket.
- Setup wizard displays the MCP SSE endpoint prominently in a highlighted box.

### Documentation

- Architecture diagram updated to show Kai 9000 as MCP SSE client.
- Added phone-only deployment note (Termux + Kai 9000 sandbox).

---

## v2.0.0 (2026-07-14)

### Architecture Refactoring

- **Split `tools.py` into `tools/` package** — organized by domain: `device.py`, `input.py`, `apps.py`, `system.py`, `files.py`, `vision.py` + `__init__.py` with `register_all_tools(mcp)` centralized registration
- **Split `vision.py` into `vision/` package** — `models.py` (dataclasses + Protocol), `clients.py` (Anthropic + OpenAI), `prompts.py` (prompt builder + response parser)
- **Extracted `server.py`** — FastMCP definition separated from entry point, `main.py` reduced from 373 → 63 lines
- **Fixed `config.py`** — removed import-time side effect (`os.makedirs`)
- **Fixed `bridge.py`** — `_history()` → `get_history()` public API
- **Added `.gitignore`** — Python, env, IDE, OS ignores

### MCP Transport Modes

- **stdio** — local Claude Desktop integration (existing)
- **SSE (HTTP)** — `--mode mcp-sse` on port 9000, for web frontends and remote MCP clients
- **Streamable HTTP** — `--mode mcp-http`, new MCP transport spec
- **Hybrid modes** — `all-sse` (SSE + Web GUI), configurable via `MCP_HOST`/`MCP_PORT`

### Vision Model Integration (v1.0 → v2.0)

- **`vision/models.py`** — `BoundingBox`, `Element`, `VisionResult` dataclasses + `VisionClient` Protocol
- **`vision/clients.py`** — `AnthropicVisionClient` (Claude Messages API) + `OpenAIVisionClient` (GPT-4o + custom endpoints)
- **`vision/prompts.py`** — `build_vision_prompt()` precision UI locator prompt + `_parse_vision_response()` with markdown fence / trailing comma handling
- **2 new MCP tools**:
  - `find_element(description)` — AI locates UI elements, returns coordinates + bounds + confidence
  - `click_element(description)` — find AND click in one step

### Web GUI — Complete Rewrite

- **Three-column layout** — left sidebar (280px device info + quick actions + shell), center (AI chat), right (360px live screen)
- **AI Chat** — send natural language → LLM (Anthropic/OpenAI/custom) → tool execution:
  - `web/chat_agent.py` — 20-tool registry, system prompt builder, JSON response parser, multi-provider LLM routing
  - "Open settings" → `open_app()`, "Click search" → `click_element()` via vision
- **Language i18n** — zh/English toggle, `data-i18n` attributes, `I18N` translation map, first-visit picker
- **Settings Panel** — provider selector (Anthropic/OpenAI/Custom), API key with show/hide, model name, custom URL, reads/writes `.env` via `GET/POST /api/settings`
- **ADB Device Manager** — list devices, connect/disconnect wireless, enable TCP/IP, integrated in Settings
- **CSS Theme** — GitHub Dark palette, chat bubbles with animation, typing indicator, smooth modal transitions, responsive breakpoints
- **Markdown rendering** — bold, italic, code, pre blocks in chat messages
- **Timestamps** — `HH:MM` on every chat message

### scrcpy Integration

- **`web/scrcpy_bridge.py`** — process management + 10fps WebSocket frame streaming
- **Native scrcpy** — one-click launch/stop from GUI
- **Browser stream** — `▶ Play` button starts `/ws/screen` WebSocket, `● LIVE` badge with pulse animation
- **Click-to-touch** — click on the stream image sends coordinates to device
- Auto-detect scrcpy installation, grey out if missing

### Connection Setup Wizard

- **5-step guided setup** — ADB install, device connect, Android app, .env config, vision API
- **Rich details** — ADB version/path, device model/ID, Shizuku status, Android version
- **`GET /api/setup/status`** — server-side prerequisite checking
- **Auto-popup** — appears 3s after load if device disconnected

### One-Click Startup Scripts

- **`start.sh`** — cross-platform bash (Git Bash/Linux/Mac) with colored output, prerequisite checks, ADB forward, browser auto-open, `--status/--stop/--restart/--no-browser` flags
- **`start.bat`** — Windows CMD with CRLF encoding, `rem` comments, same functionality
- **`scripts/setup.sh`** — first-time setup: check prereqs → install deps → create .env → build Android APK → install to device

### Encoding Fixes

- All CLI output converted from Chinese to English to avoid Windows terminal garbling
- `main.py`, `gateway.py`, all `.sh`/`.bat` scripts, `.env.example` — all terminal-facing text in English
- `start.bat` uses CRLF line endings + `rem` comments for CMD compatibility

### Android APK Improvements

- **Bug fixes**:
  - `InputApi.typeText` — replaced `%s` space hack with base64-encoded pipe input
  - `FileApi.readFile`/`writeFile` — base64 encoding to prevent shell injection
  - `SystemApi.getDeviceInfo` — merged 6 shell calls into 1 for ~5x speedup
- **UI rewrite** — dark theme (GitHub palette), status card with Shizuku/Permission/Service/IP display, auto-start on launch
- **New features** — WiFi IP display, Shizuku binder lifecycle listener, `ACCESS_WIFI_STATE` permission
- **More key codes** — tab, escape, menu, search added to `pressKey()`

### Documentation

- **`README.md`** — English: architecture diagram, 29-tool table, quick start, config, CLI, project tree
- **`README_zh.md`** — Chinese: full translation
- **`CHANGELOG.md`** — this file

---

## File Count Summary

| Layer | Files |
|-------|-------|
| Python backend | 19 `.py` files |
| Web frontend | 3 files (`index.html`, `style.css`, `app.js`) |
| Android app | 10 files (Kotlin, XML, Gradle) |
| Scripts | 3 files (`start.sh`, `start.bat`, `scripts/setup.sh`) |
| Docs | 3 files (`README.md`, `README_zh.md`, `CHANGELOG.md`) |
| Config | 3 files (`.env.example`, `.gitignore`, `pyproject.toml`) |
| **Total** | **41 files** |
