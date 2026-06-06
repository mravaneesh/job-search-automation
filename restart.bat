@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  JobScope - restart script
rem  Kills any running web server on port 3000 (frontend),
rem  makes sure Docker + Postgres are up (backend), then starts
rem  the Next.js app. Double-click this file, or run it from a
rem  terminal. Press Ctrl+C in this window to stop the server.
rem ============================================================

rem --- this .bat lives in the repo root ---
set "ROOT=%~dp0"
set "WEB=%ROOT%web"
set "PORT=3000"
set "DOCKER=C:\Program Files\Docker\Docker\resources\bin\docker.exe"
set "DOCKER_DESKTOP=C:\Program Files\Docker\Docker\Docker Desktop.exe"

rem --- force IPv4 so Node doesn't try ::1 first and get refused ---
set "DATABASE_URL=postgresql://jobsearch:jobsearch@127.0.0.1:5432/jobsearch"

echo.
echo === [1/4] Stopping any server on port %PORT% (frontend) ===
set "KILLED="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr ":%PORT%"') do (
  echo    killing PID %%p
  taskkill /F /PID %%p >nul 2>&1
  set "KILLED=1"
)
if not defined KILLED echo    nothing was running on %PORT%

echo.
echo === [2/4] Ensuring Docker engine is running (backend) ===
"%DOCKER%" info >nul 2>&1
if errorlevel 1 (
  echo    Docker not running - launching Docker Desktop, please wait...
  start "" "%DOCKER_DESKTOP%"
  set /a tries=0
  :waitdocker
  timeout /t 6 /nobreak >nul
  "%DOCKER%" info >nul 2>&1
  if errorlevel 1 (
    set /a tries+=1
    if !tries! lss 30 goto waitdocker
    echo    ERROR: Docker engine did not start. Open Docker Desktop manually, then re-run.
    pause
    exit /b 1
  )
)
echo    Docker engine is up.

echo.
echo === [3/4] Starting Postgres database (backend) ===
pushd "%ROOT%"
"%DOCKER%" compose up -d db
popd

echo.
echo === [4/4] Starting Next.js app (frontend) on http://localhost:%PORT% ===
echo    (leave this window open; Ctrl+C to stop)
echo.
cd /d "%WEB%"
call npm run dev

endlocal
