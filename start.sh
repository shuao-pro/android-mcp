#!/usr/bin/env bash
# ============================================================
#  Android MCP Server — One-Click Start
# ============================================================
set -euo pipefail

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  OK${NC} $1"; }
err()  { echo -e "${RED}  FAIL${NC} $1"; }
warn() { echo -e "${YELLOW}  WARN${NC} $1"; }
info() { echo -e "${BLUE}  >>${NC} $1"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

banner() {
    echo -e "${BOLD}${BLUE}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║       Android MCP Server v2.0.2          ║"
    echo "  ║    Shizuku + ADB Tunnel + Vision         ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_prereqs() {
    local missing=0

    if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
        err "Python 3.10+ not found"
        missing=1
    else
        ok "Python found"
    fi

    if ! command -v adb &>/dev/null; then
        warn "adb not found (port forward skipped)"
    else
        ok "ADB found"
    fi

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        warn ".env not found, creating from defaults"
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        else
            cat > "$PROJECT_DIR/.env" << 'EOF'
ANDROID_HOST=127.0.0.1
ANDROID_PORT=18080
WEB_HOST=127.0.0.1
WEB_PORT=8080
MCP_HOST=0.0.0.0
MCP_PORT=9000
SCREENSHOT_DIR=./screenshots
REQUEST_TIMEOUT=30.0
EOF
        fi
        ok ".env created"
    else
        ok ".env found"
    fi

    return $missing
}

setup_adb() {
    info "Checking ADB connection..."

    local devices
    devices=$(adb devices 2>/dev/null | tail -n +2 | grep -v '^$' | grep -v 'offline' | wc -l)
    if [ "$devices" -eq 0 ]; then
        warn "No ADB device connected"
        info "  USB: connect phone, enable USB Debugging"
        info "  Wireless: adb connect <ip>:5555"
        return 1
    fi
    ok "Device connected"

    info "Setting up port forward (18080 -> 18080)..."
    adb forward tcp:18080 tcp:18080 2>/dev/null && \
        ok "Port forward: tcp:18080 -> tcp:18080" || \
        warn "Port forward may already exist"
}

check_android_service() {
    info "Checking Android MCP service..."

    local health
    if command -v curl &>/dev/null; then
        health=$(curl -s --connect-timeout 3 --max-time 8 http://127.0.0.1:18080/health 2>/dev/null || echo "")
    elif command -v python3 &>/dev/null; then
        health=$(python3 -c "
import urllib.request
try:
    resp = urllib.request.urlopen('http://127.0.0.1:18080/health', timeout=3)
    print(resp.read().decode())
except: print('')
" 2>/dev/null)
    else
        health=""
    fi

    if echo "$health" | grep -q '"connected":true'; then
        ok "Android MCP service is running"
        return 0
    else
        warn "Android MCP service not reachable"
        info "On your device:"
        info "  1. Start Shizuku app (grant root/ADB permission)"
        info "  2. Open Android MCP app (grant Shizuku permission)"
        info "  3. App shows notification: MCP service running"
        return 1
    fi
}

open_browser() {
    local url="${1:-http://127.0.0.1:8080}"

    # Open browser in background after a brief delay for server startup
    (
        sleep 1.5
        if command -v python3 &>/dev/null; then
            python3 -c "import webbrowser; webbrowser.open('$url')" 2>/dev/null
        elif command -v python &>/dev/null; then
            python -c "import webbrowser; webbrowser.open('$url')" 2>/dev/null
        elif command -v xdg-open &>/dev/null; then
            xdg-open "$url" 2>/dev/null
        elif command -v open &>/dev/null; then
            open "$url" 2>/dev/null
        elif command -v start &>/dev/null; then
            start "$url" 2>/dev/null
        fi
    ) &
}

start_server() {
    echo ""
    banner

    set -a; source "$PROJECT_DIR/.env" 2>/dev/null || true; set +a

    local web_port="${WEB_PORT:-8080}"
    local mcp_port="${MCP_PORT:-9000}"
    local mcp_host="${MCP_HOST:-0.0.0.0}"

    # Detect LAN IP
    local lan_ip="127.0.0.1"
    if command -v python3 &>/dev/null; then
        lan_ip=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(0.1); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "127.0.0.1")
    fi

    if [ "${NO_BROWSER:-0}" != "1" ]; then
        info "Opening browser at http://127.0.0.1:${web_port} ..."
        open_browser "http://127.0.0.1:${web_port}"
    fi

    echo ""
    echo "  =============================================="
    echo "    MCP Endpoints (port ${mcp_port}):"
    echo "      SSE:            http://127.0.0.1:${mcp_port}/sse"
    echo "      Streamable HTTP: http://127.0.0.1:${mcp_port}/mcp"
    if [ "$lan_ip" != "127.0.0.1" ]; then
        echo "      LAN SSE:        http://${lan_ip}:${mcp_port}/sse"
        echo "      LAN HTTP:       http://${lan_ip}:${mcp_port}/mcp"
    fi
    echo ""
    echo "    Kai 9000  →  use the /mcp endpoint"
    echo "    Claude Desktop  →  use the /sse endpoint"
    echo "    Web GUI:  http://127.0.0.1:${web_port}"
    echo "  =============================================="
    echo ""

    cd "$PROJECT_DIR"
    exec python3 -m android_mcp.main --mode all-sse 2>&1 || \
        exec python -m android_mcp.main --mode all-sse
}

show_status() {
    banner
    echo ""

    if command -v adb &>/dev/null; then
        local devs
        devs=$(adb devices 2>/dev/null | tail -n +2 | grep -v '^$' | wc -l)
        [ "$devs" -gt 0 ] && ok "ADB: $devs device(s)" || warn "ADB: no device"
    else
        warn "ADB: not installed"
    fi

    if command -v curl &>/dev/null; then
        curl -s --connect-timeout 2 --max-time 4 http://127.0.0.1:18080/health &>/dev/null && \
            ok "Android MCP: running (port 18080)" || \
            warn "Android MCP: not reachable (port 18080)"
    fi

    if command -v curl &>/dev/null; then
        curl -s --connect-timeout 2 --max-time 4 http://127.0.0.1:8080/ &>/dev/null && \
            ok "Web GUI: http://127.0.0.1:8080" || \
            warn "Web GUI: not running"
        curl -s --connect-timeout 2 --max-time 4 http://127.0.0.1:9000/health &>/dev/null && \
            ok "MCP Server: http://127.0.0.1:9000 (SSE + Streamable HTTP)" || \
            warn "MCP Server: not running (port 9000)"
    fi

    local pid_dir="$HOME/.android-mcp"
    if [ -f "$pid_dir/mcp.pid" ]; then
        local pid; pid=$(cat "$pid_dir/mcp.pid")
        if kill -0 "$pid" 2>/dev/null; then
            ok "MCP PID: $pid (alive)"
        else
            warn "MCP PID: $pid (stale)"
        fi
    fi
    if [ -f "$pid_dir/web.pid" ]; then
        local pid; pid=$(cat "$pid_dir/web.pid")
        if kill -0 "$pid" 2>/dev/null; then
            ok "Web PID: $pid (alive)"
        else
            warn "Web PID: $pid (stale)"
        fi
    fi
}

stop_services() {
    echo -e "${BOLD}Stopping Android MCP services...${NC}"
    local pid_dir="$HOME/.android-mcp"

    for svc in mcp web; do
        if [ -f "$pid_dir/$svc.pid" ]; then
            local pid; pid=$(cat "$pid_dir/$svc.pid")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null && ok "Stopped $svc (PID: $pid)" || \
                    err "Failed to stop $svc"
            fi
            rm -f "$pid_dir/$svc.pid"
        fi
    done

    python3 -m android_mcp.gateway stop 2>/dev/null || true
    ok "All services stopped"
}

case "${1:-}" in
    --status|-s)
        show_status
        ;;
    --stop|-k)
        stop_services
        ;;
    --restart|-r)
        stop_services
        sleep 1
        check_prereqs || true
        setup_adb || true
        echo "  Tip: Start Shizuku + Android MCP app on your phone"
        echo "  to enable full device control (port 18080)."
        start_server
        ;;
    --help|-h)
        echo "Usage: ./start.sh [--status|--stop|--restart|--no-browser|--help]"
        echo ""
        echo "  (no args)     Start MCP Server + Web GUI + ADB forward"
        echo "  --no-browser  Start without opening browser"
        echo "  --status      Show service status"
        echo "  --stop        Stop all services"
        echo "  --restart     Restart all services"
        echo "  --help        This help"
        ;;
    --no-browser)
        NO_BROWSER=1
        check_prereqs
        echo ""
        setup_adb
        echo ""
        echo "  Tip: Start Shizuku + Android MCP app on your phone"
        echo "  to enable full device control (port 18080)."
        echo ""
        start_server
        ;;
    *)
        check_prereqs
        echo ""
        setup_adb
        echo ""
        echo "  Tip: Start Shizuku + Android MCP app on your phone"
        echo "  to enable full device control (port 18080)."
        echo ""
        start_server
        ;;
esac
