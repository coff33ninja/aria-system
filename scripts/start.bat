@echo off
REM Aria System - Windows Start Script (Desktop Mode)

echo ============================================
echo   Aria System - Desktop Mode
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
echo [*] Starting Aria Desktop Mode...
echo.
echo Frontend will open in browser (or use Electron for desktop avatar)
echo Press Ctrl+C to stop
echo.

python -m desktop.agent
