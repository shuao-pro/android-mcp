"""End-to-end ADB test for Android MCP bridge — requires connected device."""
import asyncio, sys, os, base64, subprocess

passed = 0; failed = 0

def test(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")

async def main():
    global passed, failed

    # 1. ADB + Device
    print("=== ADB & Device ===")
    r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
    lines = [l for l in r.stdout.strip().split("\n") if l and "List" not in l]
    has_device = len(lines) > 0
    test("ADB available", r.returncode == 0)
    test("Device connected", has_device)
    if not has_device:
        print("\n  No device found. Connect phone via USB or WiFi ADB.")
        return

    # 2. Port forward
    print("\n=== Port Forward ===")
    subprocess.run(["adb", "forward", "tcp:18080", "tcp:18080"],
                   capture_output=True, timeout=5)
    r = subprocess.run(["adb", "forward", "--list"], capture_output=True, text=True, timeout=5)
    test("Port 18080 forwarded", "tcp:18080" in r.stdout)

    # 3. Health check
    print("\n=== Health Check ===")
    from android_mcp.bridge.device import health_check
    h = await health_check()
    connected = h.get("connected", False)
    test("Device health check", connected)
    test("Shizuku running", h.get("shizuku_running", False))
    if not connected:
        print("\n  Device not reachable. Ensure Shizuku + Android MCP app running.")
        return

    # 4. Device info
    print("\n=== Device Info ===")
    from android_mcp.bridge.device import get_device_info
    info = await get_device_info()
    ok = info.get("success", False)
    test("get_device_info success", ok)
    if ok:
        d = info if "model" in info else info.get("data", {})
        for k in ["model", "os_version", "screen_resolution", "manufacturer"]:
            if k in d:
                print(f"       {k}: {d[k]}")
    else:
        err = info.get("error", "unknown")
        print(f"       error: {err}")

    # 5. Screenshot (ADB fast path)
    print("\n=== Screenshot ===")
    from android_mcp.bridge.device import fast_screenshot, get_screenshot
    fs = await fast_screenshot()
    test("fast_screenshot success", fs.get("success", False))
    if fs.get("success"):
        img = fs["data"]["base64"]
        os.makedirs("screenshots", exist_ok=True)
        path = "screenshots/test_adb.png"
        with open(path, "wb") as f:
            f.write(base64.b64decode(img))
        test(f"Screenshot saved ({len(img)} chars)", os.path.exists(path))
    else:
        ss = await get_screenshot()
        test("get_screenshot (HTTP fallback)", ss.get("success", False))

    # 6. Shell
    print("\n=== Shell ===")
    from android_mcp.bridge.device import shell
    r = await shell("echo HELLO_MCP_TEST")
    test("shell echo", r.get("success", False) and "HELLO_MCP_TEST" in str(r))
    r2 = await shell("getprop ro.build.version.sdk")
    test("shell getprop sdk", r2.get("success", False))
    if r2.get("success"):
        stdout = r2.get("stdout", str(r2))
        print(f"       SDK: {stdout.strip()}")

    # 7. Current app
    print("\n=== Current App ===")
    from android_mcp.bridge.apps import get_current_app
    r = await get_current_app()
    test("get_current_app", r.get("success", False))
    if r.get("success"):
        stdout = r.get("stdout", str(r))
        print(f"       foreground: {stdout.strip()[:80]}")

    # 8. Battery
    print("\n=== Battery ===")
    from android_mcp.bridge.system import get_battery_info
    r = await get_battery_info()
    ok = r.get("success", False)
    test("get_battery_info", ok)
    if ok:
        d = r if "model" in r else r.get("data", r)
        bl = d.get("battery_level", "N/A")
        print(f"       level: {bl}")

    # 9. Installed apps
    print("\n=== Apps ===")
    from android_mcp.bridge.apps import list_installed_apps
    r = await list_installed_apps()
    ok = r.get("success", False)
    test("list_installed_apps", ok)
    if ok:
        pkgs = r.get("packages", r.get("data", []))
        count = len(pkgs) if isinstance(pkgs, list) else r.get("count", 0)
        print(f"       count: {count}")

    # 10. Clipboard (read-only)
    print("\n=== Clipboard ===")
    from android_mcp.bridge.system import get_clipboard
    r = await get_clipboard()
    test("get_clipboard", r.get("success", False))
    if r.get("success") and r.get("text"):
        print(f"       content: {r['text'][:50]}")

    # Summary
    print(f"\n{'='*50}")
    print(f"  {passed} PASS, {failed} FAIL  ({passed + failed} total)")
    print(f"{'='*50}")

asyncio.run(main())