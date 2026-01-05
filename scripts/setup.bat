@echo off
REM Aria System - Windows Setup Script
REM Tested on Python 3.12, Node.js 18+

echo ============================================
echo   Aria System - Setup (Windows)
echo ============================================
echo.

REM Change to project root (parent of scripts folder)
cd /d "%~dp0.."

echo [*] Working directory: %CD%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.12+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Create virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate venv and install requirements
echo.
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [*] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Check for .env file
echo.
if not exist ".env" (
    echo [*] Creating .env from template...
    copy .env.sample .env >nul
    echo [!] Please edit .env with your API keys before running
) else (
    echo [OK] .env file exists
)

REM Create data directory
if not exist "data" (
    echo [*] Creating data directory...
    mkdir data
)

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Edit .env with your API keys
echo   2. Run: scripts\start.bat
echo.
echo For Electron desktop avatar (optional):
echo   cd desktop\electron
echo   npm install
echo.
pause
