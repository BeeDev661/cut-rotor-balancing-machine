#!/bin/bash

# Quick Start Script for Linux/macOS
# This script sets up and starts the dashboard

echo ""
echo "========================================"
echo " Rotor Balancing Dashboard - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

echo "[1/5] Checking virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "[2/5] Activating virtual environment..."
source .venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt

echo "[4/5] Verifying .env file..."
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo "[5/5] Starting services..."
echo ""
echo "Choose an option:"
echo "1) Backend only (port 8000)"
echo "2) Dashboard only (port 8501) - requires running backend"
echo "3) Both (in background)"
echo "4) Exit"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Starting FastAPI backend..."
        uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
        ;;
    2)
        echo "Starting Streamlit dashboard..."
        streamlit run frontend/streamlit_app.py
        ;;
    3)
        echo "Starting backend in background..."
        nohup uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
        BACKEND_PID=$!
        echo "Backend PID: $BACKEND_PID"
        
        sleep 2
        
        echo "Starting dashboard..."
        streamlit run frontend/streamlit_app.py
        
        echo ""
        echo "Backend running in background (PID: $BACKEND_PID)"
        echo ""
        echo "Backend: http://127.0.0.1:8000"
        echo "Dashboard: http://127.0.0.1:8501"
        echo ""
        echo "To stop backend: kill $BACKEND_PID"
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
