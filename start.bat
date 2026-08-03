@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "BACKEND_PORT=8001"
set "FRONTEND_PORT=5173"
set "ROOT_DIR=%~dp0"

echo ==========================================
echo   OfferFlow Job Hunting Assistant
echo ==========================================
echo.

REM --- Environment checks ---
if not exist "%ROOT_DIR%.venv\Scripts\python.exe" (
    echo [ERROR] Virtual env not found: .venv\Scripts\python.exe
    echo         Run "uv sync" first.
    pause
    exit /b 1
)

if not exist "%ROOT_DIR%.env" (
    echo [WARN] .env not found. Copied from .env.example.
    copy "%ROOT_DIR%.env.example" "%ROOT_DIR%.env" >nul
    echo [ERROR] Please fill required environment variables in .env, then run again.
    pause
    exit /b 1
)

findstr /B /C:"ENCRYPTION_KEY=" "%ROOT_DIR%.env" >nul 2>&1
if errorlevel 1 (
    echo [WARN] ENCRYPTION_KEY not found in .env. Model settings cannot save API keys.
)

if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [WARN] Frontend dependencies missing. Running npm install...
    pushd "%ROOT_DIR%frontend"
    call npm install
    if errorlevel 1 (
        popd
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    popd
)

REM --- Port checks ---
set "SKIP_BACKEND=0"
set "SKIP_FRONTEND=0"

netstat -ano | findstr /C:":%BACKEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port %BACKEND_PORT% is already in use. Skipping backend.
    set "SKIP_BACKEND=1"
)

netstat -ano | findstr /C:":%FRONTEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port %FRONTEND_PORT% is already in use. Skipping frontend.
    set "SKIP_FRONTEND=1"
)

REM --- Start services ---
if "!SKIP_BACKEND!"=="0" (
    echo [1/2] Starting backend on port %BACKEND_PORT% ...
    start "OfferFlow Backend" cmd /k "cd /d ""%ROOT_DIR%"" && set UVICORN_RELOAD=true && set PORT=%BACKEND_PORT% && .venv\Scripts\python.exe run.py"
)

if "!SKIP_FRONTEND!"=="0" (
    echo [2/2] Starting frontend on port %FRONTEND_PORT% ...
    start "OfferFlow Frontend" cmd /k "cd /d ""%ROOT_DIR%frontend"" && npm run dev"
)

REM --- Wait for backend ---
if "!SKIP_BACKEND!"=="0" (
    echo.
    echo Waiting for backend to be ready ...
    set "TRIES=0"
    call :wait_backend
    if errorlevel 1 goto done
    echo Backend is ready.
)

REM --- Wait for frontend ---
if "!SKIP_FRONTEND!"=="0" (
    echo Waiting for frontend to be ready ...
    set "TRIES=0"
    call :wait_frontend
    if errorlevel 1 goto done
    echo Frontend is ready.
)

:done
echo.
echo ==========================================
echo   Startup finished!
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%
echo   API Docs: http://127.0.0.1:%BACKEND_PORT%/docs
echo   Frontend: http://127.0.0.1:%FRONTEND_PORT%
echo ==========================================
echo.
echo To stop, close the backend/frontend windows.
echo Press any key to exit...
pause >nul
exit /b 0

:wait_backend
set "HEALTH="
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:%BACKEND_PORT%/api/health' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }" > "%TEMP%\offerflow_health.txt" 2>nul
set /p HEALTH=<"%TEMP%\offerflow_health.txt"
if "!HEALTH!"=="200" exit /b 0
timeout /t 1 /nobreak >nul
set /a TRIES+=1
if !TRIES! lss 30 goto wait_backend
echo [WARN] Backend did not become ready within 30 seconds.
exit /b 1

:wait_frontend
set "READY="
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:%FRONTEND_PORT%/' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }" > "%TEMP%\offerflow_frontend.txt" 2>nul
set /p READY=<"%TEMP%\offerflow_frontend.txt"
if "!READY!"=="200" exit /b 0
timeout /t 1 /nobreak >nul
set /a TRIES+=1
if !TRIES! lss 30 goto wait_frontend
echo [WARN] Frontend did not become ready within 30 seconds.
exit /b 1
