"""
Diagnostic tool to verify dashboard setup and connections.
Run: python backend/diagnostics.py
"""

import os
import sys
import asyncio
import json
from datetime import datetime

print("=" * 60)
print("Dashboard Diagnostic Tool")
print("=" * 60)
print()

# Check 1: Python Version
print("[1/8] Checking Python version...")
print(f"  Python: {sys.version}")
if sys.version_info < (3, 9):
    print("  ⚠️  WARNING: Python 3.9+ recommended")
else:
    print("  ✓ OK")
print()

# Check 2: Virtual Environment
print("[2/8] Checking virtual environment...")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"  Virtual environment: Active")
    print(f"  Path: {sys.prefix}")
    print("  ✓ OK")
else:
    print("  ⚠️  WARNING: Not running in virtual environment")
print()

# Check 3: Required Packages
print("[3/8] Checking required packages...")
required_packages = [
    'fastapi',
    'uvicorn',
    'numpy',
    'streamlit',
    'websocket',
    'requests',
    'plotly',
    'paho',
    'pydantic',
    'passlib',
    'jwt',
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package)
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} (MISSING)")
        missing_packages.append(package)

if missing_packages:
    print(f"\n  Install missing packages with:")
    print(f"  pip install {' '.join(missing_packages)}")
else:
    print("  ✓ All packages installed")
print()

# Check 4: Configuration Files
print("[4/8] Checking configuration files...")
config_files = [
    '.env',
    'requirements.txt',
    'backend/main.py',
    'backend/mqtt_handler.py',
    'frontend/streamlit_app.py',
]

for file in config_files:
    if os.path.exists(file):
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ {file} (MISSING)")
print()

# Check 5: Environment Variables
print("[5/8] Checking environment configuration...")
from dotenv import load_dotenv
load_dotenv()

mqtt_enabled = os.getenv("USE_MQTT", "false").lower() == "true"
mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
mqtt_port = os.getenv("MQTT_PORT", "1883")

print(f"  MQTT Enabled: {mqtt_enabled}")
print(f"  MQTT Broker: {mqtt_broker}:{mqtt_port}")
print(f"  MQTT User: {os.getenv('MQTT_USER', '(not set)')}")
print(f"  Dashboard Secret: {'**' + os.getenv('DASHBOARD_SECRET', 'change_this_secret')[-10:] if os.getenv('DASHBOARD_SECRET') else '(not set)'}")
print()

# Check 6: MQTT Connectivity (if enabled)
print("[6/8] Checking MQTT broker connectivity...")
if mqtt_enabled:
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(client_id="diagnostic_client")
        
        result = client.connect(mqtt_broker, int(mqtt_port), keepalive=1)
        
        if result == 0:
            print(f"  ✓ Successfully connected to {mqtt_broker}:{mqtt_port}")
            client.disconnect()
        else:
            print(f"  ✗ Connection failed with error code {result}")
    except Exception as e:
        print(f"  ✗ Error connecting to MQTT: {e}")
else:
    print("  ℹ MQTT disabled (using simulator mode)")
print()

# Check 7: Port Availability
print("[7/8] Checking port availability...")
import socket

ports = {
    8000: "Backend (FastAPI)",
    8501: "Dashboard (Streamlit)",
    1883: "MQTT",
}

for port, service in ports.items():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        print(f"  ⚠️  Port {port} ({service}): Already in use")
    else:
        print(f"  ✓ Port {port} ({service}): Available")
    sock.close()
print()

# Check 8: Database
print("[8/8] Checking database...")
db_path = os.path.join(os.path.dirname(__file__), "users.db")
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"  ✓ Database exists: {db_path}")
    print(f"    Size: {size} bytes")
else:
    print(f"  ℹ Database will be created on first run")
print()

# Summary
print("=" * 60)
print("Diagnostic Summary")
print("=" * 60)

if not missing_packages:
    print("✓ All checks passed!")
    print()
    print("Next steps:")
    if mqtt_enabled:
        print("1. Verify ESP32 is connected to MQTT broker")
        print("2. Check ESP32 is publishing to:")
        print("   - esp32/accelerometer")
        print("   - esp32/rpm")
        print("3. Start backend: uvicorn backend.main:app --reload")
        print("4. Start dashboard: streamlit run frontend/streamlit_app.py")
    else:
        print("1. Start backend: uvicorn backend.main:app --reload")
        print("2. Start dashboard: streamlit run frontend/streamlit_app.py")
        print("3. Use simulator mode to test")
        print("4. When ready, enable MQTT in .env file")
else:
    print("✗ Some packages are missing!")
    print()
    print("Fix with:")
    print(f"  pip install {' '.join(missing_packages)}")

print()
print("For more help, see SETUP_GUIDE.md")
print("=" * 60)
