@echo off
REM Quick Start Script for Windows
REM This script sets up and starts the dashboard with simulator mode

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Rotor Balancing Dashboard - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt

echo [4/5] Verifying .env file...
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
)

echo [5/5] Starting services...
echo.
echo Choose an option:
echo 1) Backend only (port 8000)
echo 2) Dashboard only (port 8501) - requires running backend
echo 3) Both (in separate windows)
echo 4) Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo Starting FastAPI backend...
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
) else if "%choice%"=="2" (
    echo Starting Streamlit dashboard...
    streamlit run frontend/streamlit_app.py
) else if "%choice%"=="3" (
    echo Starting backend in new window...
    start cmd /k "cd /d %cd% && .venv\Scripts\activate && uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
    
    timeout /t 3 /nobreak
    
    echo Starting dashboard in new window...
    start cmd /k "cd /d %cd% && .venv\Scripts\activate && streamlit run frontend/streamlit_app.py"
    
    echo.
    echo Both services started!
    echo.
    echo Backend: http://127.0.0.1:8000
    echo Dashboard: http://127.0.0.1:8501
    echo.
    echo Press any key to exit this window...
    pause
) else (
    echo Exiting...
    exit /b 0
)
