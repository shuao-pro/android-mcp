#!/usr/bin/env bash
# ============================================================
#  Android MCP Server — First-Time Setup
# ============================================================
set -euo pipefail

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
NC='\033[0m'

ok()    { echo -e "${GREEN}  OK${NC} $1"; }
err()   { echo -e "${RED}  FAIL${NC} $1"; }
warn()  { echo -e "${YELLOW}  WARN${NC} $1"; }
info()  { echo -e "${BLUE}  >>${NC} $1"; }
step()  { echo -e "\n${BOLD}${BLUE}== $1${NC}"; }

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BOLD}"
echo "=============================================="
echo "  Android MCP Server — Setup"
echo "=============================================="
echo -e "${NC}"

# -------- Step 1: Check prerequisites --------
step "Step 1/5: Checking prerequisites"

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    err "Python 3.10+ not found. Install from https://python.org"
    exit 1
fi
PY_VER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
ok "Python $PY_VER"

if ! command -v adb &>/dev/null; then
    err "adb not found. Install Android SDK Platform Tools."
    exit 1
fi
ok "ADB $(adb version 2>&1 | head -1)"

# -------- Step 2: Install Python deps --------
step "Step 2/5: Installing Python dependencies"

if command -v uv &>/dev/null; then
    uv pip install -e "$PROJECT_DIR" 2>/dev/null || pip install -e "$PROJECT_DIR"
    ok "Dependencies installed (uv)"
else
    pip install -e "$PROJECT_DIR" 2>/dev/null
    ok "Dependencies installed (pip)"
fi

# -------- Step 3: Configure .env --------
step "Step 3/5: Configuring environment"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        ok ".env created from .env.example"
        warn "Edit .env to set your API keys for vision features"
    else
        cat > "$PROJECT_DIR/.env" << 'EOF'
ANDROID_HOST=127.0.0.1
ANDROID_PORT=18080
REQUEST_TIMEOUT=30.0
WEB_HOST=127.0.0.1
WEB_PORT=8080
SCREENSHOT_DIR=./screenshots
# VISION_PROVIDER=anthropic
# VISION_API_KEY=sk-ant-api03-xxxxx
EOF
        ok ".env created with defaults"
    fi
else
    ok ".env already exists"
fi

# -------- Step 4: Build and install Android app --------
step "Step 4/5: Building Android app"

ANDROID_APP_DIR="$PROJECT_DIR/android-app"
if [ -d "$ANDROID_APP_DIR" ]; then
    if [ -f "$ANDROID_APP_DIR/gradlew" ]; then
        info "Building APK (this may take a few minutes)..."
        (cd "$ANDROID_APP_DIR" && bash gradlew assembleDebug 2>&1 | tail -3)
        APK=$(find "$ANDROID_APP_DIR" -name "*.apk" -path "*/debug/*" | head -1)
        if [ -n "$APK" ]; then
            ok "APK built: $APK"
        else
            warn "APK build may have failed. Check Android SDK setup."
        fi
    else
        warn "No Gradle wrapper found. Open android-app/ in Android Studio to build."
        warn "Or: cd android-app && gradle wrapper"
    fi
else
    warn "android-app/ directory not found, skipping APK build"
fi

# -------- Step 5: Connect device --------
step "Step 5/5: Device setup"

DEVICES=$(adb devices 2>/dev/null | tail -n +2 | grep -v '^$' | wc -l)
if [ "$DEVICES" -eq 0 ]; then
    warn "No ADB device connected"
    info "Connect via USB and enable USB Debugging, or:"
    info "  adb connect <device-ip>:5555"
else
    ok "$DEVICES device(s) connected"
    adb devices 2>/dev/null | tail -n +2 | grep -v '^$'
fi

if [ -n "${APK:-}" ]; then
    info "Installing APK on device..."
    adb install -r "$APK" 2>/dev/null && ok "APK installed" || warn "APK install failed (check device connection)"
fi

info "Setting up ADB forward (tcp:18080 -> tcp:18080)..."
adb forward tcp:18080 tcp:18080 2>/dev/null && ok "ADB forward configured" || warn "ADB forward failed"

# -------- Done --------
echo ""
echo -e "${GREEN}${BOLD}=============================================="
echo "  Setup Complete!"
echo "==============================================${NC}"
echo ""
echo -e "  Next steps:"
echo -e "  1. On your Android device, open Shizuku and start it"
echo -e "  2. Open the Android MCP app (grant Shizuku permission)"
echo -e "  3. Run: ./start.sh"
echo -e "  4. Open http://127.0.0.1:8080 in browser"
echo ""
