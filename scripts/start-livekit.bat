@echo off
REM Aria Maid System - Windows LiveKit Mode Start Script

echo ============================================
echo   Aria Maid System - LiveKit Mode
echo ============================================
echo.

REM Change to project root (parent of scripts folder)
cd /d "%~dp0.."

echo [*] Working directory: %CD%

REM Check if venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] Virtual environment not found.
    echo Please run: scripts\setup.bat
    pause
    exit /b 1
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Check for .env
if not exist ".env" (
    echo.
    echo [ERROR] .env file not found.
    echo Please copy .env.sample to .env and add your API keys.
    pause
    exit /b 1
)

echo [OK] Environment ready
echo.
echo [*] Starting Aria LiveKit Mode...
echo.
echo Requires LiveKit credentials in .env
echo Press Ctrl+C to stop
echo.

python -m livekit_mode.agent dev
