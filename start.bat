@echo off
setlocal enabledelayedexpansion
rem ============================================================
rem  Android MCP Server — Windows One-Click Start
rem ============================================================

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

rem -------- Banner --------
echo.
echo   ==============================================
echo     Android MCP Server v2.0.2
echo     Shizuku + ADB Tunnel + Vision
echo   ==============================================
echo.

rem -------- Args --------
if /i "%~1"=="--help" goto :help
if /i "%~1"=="-h" goto :help
if /i "%~1"=="--status" goto :status
if /i "%~1"=="-s" goto :status
if /i "%~1"=="--stop" goto :stop
if /i "%~1"=="-k" goto :stop
if /i "%~1"=="--restart" goto :restart
if /i "%~1"=="-r" goto :restart
if /i "%~1"=="--no-browser" set "NO_BROWSER=1"

rem -------- Default: Start --------

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo   [OK] Python found

adb version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] adb not found. Port forward skipped.
) else (
    echo   [OK] ADB found
    for /f "tokens=1 skip=1" %%d in ('adb devices 2^>nul ^| findstr /v "^$"') do set "HAS_DEVICE=1"
    if defined HAS_DEVICE (
        echo   [OK] Device connected
    ) else (
        echo   [WARN] No device connected. Connect via USB or wireless ADB.
    )
    adb forward tcp:18080 tcp:18080 >nul 2>&1 && (
        echo   [OK] Port forward: tcp:18080 -^> tcp:18080
    ) || (
        echo   [WARN] Port forward may already exist
    )
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo   [OK] .env created from .env.example
    ) else (
        echo   [WARN] No .env file found
    )
) else (
    echo   [OK] .env found
)

echo.
echo   Tip: Start Shizuku + Android MCP app on your phone
echo   to enable full device control (port 18080).
echo.

echo   ==============================================
echo     MCP Endpoints (port 9000):
echo       SSE:            http://127.0.0.1:9000/sse
echo       Streamable HTTP: http://127.0.0.1:9000/mcp
echo.
echo     Kai 9000  -^>  use the /mcp endpoint
echo     Claude Desktop  -^>  use the /sse endpoint
echo     Web GUI:  http://127.0.0.1:8080
echo   ==============================================
echo.

if not defined NO_BROWSER (
    echo   Opening browser...
    start "" http://127.0.0.1:8080
)

python -m android_mcp.main --mode all-sse
goto :end

rem -------- Status --------
:status
echo   Service Status:
echo   --------------
adb devices 2>nul | findstr /v "List of devices" | findstr /v "^$" >nul && (
    echo   [OK] ADB device connected
) || (
    echo   [WARN] No ADB device
)
curl -s --connect-timeout 2 --max-time 4 http://127.0.0.1:18080/health 2>nul | findstr "connected" >nul && (
    echo   [OK] Android MCP: running (port 18080)
) || (
    echo   [WARN] Android MCP: not reachable
)
curl -s --connect-timeout 2 --max-time 4 http://127.0.0.1:8080/ 2>nul >nul && (
    echo   [OK] Web GUI: http://127.0.0.1:8080
) || (
    echo   [WARN] Web GUI: not running
)
if exist "%USERPROFILE%\.android-mcp\mcp.pid" (
    set /p MCP_PID=<"%USERPROFILE%\.android-mcp\mcp.pid"
    echo   [INFO] MCP PID: !MCP_PID!
)
if exist "%USERPROFILE%\.android-mcp\web.pid" (
    set /p WEB_PID=<"%USERPROFILE%\.android-mcp\web.pid"
    echo   [INFO] Web PID: !WEB_PID!
)
goto :end

rem -------- Stop --------
:stop
echo   Stopping Android MCP services...
python -m android_mcp.gateway stop 2>nul
if exist "%USERPROFILE%\.android-mcp\mcp.pid" del "%USERPROFILE%\.android-mcp\mcp.pid"
if exist "%USERPROFILE%\.android-mcp\web.pid" del "%USERPROFILE%\.android-mcp\web.pid"
echo   [OK] Services stopped
goto :end

rem -------- Stop subroutine (for restart) --------
:stop_svc
echo   Stopping Android MCP services...
python -m android_mcp.gateway stop 2>nul
if exist "%USERPROFILE%\.android-mcp\mcp.pid" del "%USERPROFILE%\.android-mcp\mcp.pid"
if exist "%USERPROFILE%\.android-mcp\web.pid" del "%USERPROFILE%\.android-mcp\web.pid"
echo   [OK] Services stopped
goto :eof

rem -------- Restart --------
:restart
call :stop_svc
timeout /t 2 /nobreak >nul
echo.
echo   Restarting...
echo.
goto :start_default

rem -------- Help --------
:help
echo   Usage: start.bat [--status^|--stop^|--restart^|--no-browser^|--help]
echo.
echo     (no args)     Start MCP Server + Web GUI + ADB forward
echo     --no-browser  Start without opening browser
echo     --status      Show service status
echo     --stop        Stop all services
echo     --restart     Restart all services
echo     --help        This help
goto :end

rem -------- Default start (used by restart) --------
:start_default
python -m android_mcp.main --mode all-sse
rem Fall through to :end

:end
endlocal
