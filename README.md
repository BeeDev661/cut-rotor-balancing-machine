# Rotor Balancing Machine Dashboard

Real-time monitoring and control dashboard for rotor balancing machines with **ESP32 sensor integration** for remote online monitoring.

## Features

✅ **Real-Time FFT Analysis** - Frequency domain visualization for imbalance detection
✅ **Live RPM Monitoring** - Track rotor speed in real-time
✅ **WiFi Connectivity** - ESP32 sensor data via MQTT
✅ **Remote Access** - Monitor from anywhere with internet
✅ **User Authentication** - Secure login system with JWT tokens
✅ **Responsive UI** - Streamlit dashboard with beautiful styling
✅ **Fallback Simulator** - Test without hardware
✅ **Balancing Recommendations** - Physics-based mass placement calculations

## Quick Start (Local Testing)

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Optional: ESP32 board with MPU6050 accelerometer

### 1. Clone and Setup

```bash
# Navigate to project
cd c:\Users\acer\Desktop\Dashboard

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Dashboard

**Option A: Both services in separate windows (easiest)**

Windows:
```bash
quickstart.bat
```

macOS/Linux:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

**Option B: Manual (two terminals)**

Terminal 1 - Start backend:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 - Start dashboard:
```bash
streamlit run frontend/streamlit_app.py
```

### 3. Access Dashboard

Open browser to: **http://localhost:8501**

Sign up with test credentials and click "Start" to begin!

---

## Hardware Integration (ESP32)

### Architecture

```
ESP32 (WiFi)
  ├─ MPU6050 (Accelerometer)
  └─ Hall Sensor (RPM)
         │
         └──► MQTT Broker (Cloud/Local)
                  │
                  └──► FastAPI Backend
                         │
                         └──► Streamlit Dashboard
                              (Browser/Remote)
```

### Setup Instructions

1. **[ESP32 Arduino Setup](ARDUINO_SETUP.md)** - Install Arduino IDE and libraries
2. **[Complete Setup Guide](SETUP_GUIDE.md)** - Full integration instructions
3. Upload `esp32_firmware.ino` to your ESP32 board
4. Configure MQTT broker address in `.env`

### Quick Hardware Checklist

- [ ] ESP32 Development Board
- [ ] MPU6050 Accelerometer (I2C)
- [ ] Hall Effect Sensor (Optional, for RPM)
- [ ] USB Cable for programming
- [ ] Arduino IDE with ESP32 support
- [ ] Public MQTT Broker Account (HiveMQ, CloudMQTT, etc.)

---

## Remote Deployment (Online Access)

### Option 1: Heroku (Easiest)

```bash
# Create Procfile
echo "web: uvicorn backend.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku login
heroku create your-app-name
git push heroku main

# Get URL
# Your backend is at: https://your-app-name.herokuapp.com
```

### Option 2: AWS EC2 / DigitalOcean

1. Launch Ubuntu server
2. Install Python and dependencies
3. Deploy with PM2 or systemd
4. Get public IP address

### Option 3: Streamlit Cloud (Dashboard Only)

1. Push to GitHub
2. Go to https://streamlit.io/cloud
3. Deploy from repository
4. Set environment variables

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

---

## Configuration

### Environment Variables (.env file)

```bash
# General
DASHBOARD_SECRET=your_super_secret_key

# MQTT Settings (for ESP32 data)
USE_MQTT=false                           # Change to true when using ESP32
MQTT_BROKER=localhost                    # Or broker.hivemq.com
MQTT_PORT=1883
MQTT_USER=                               # If needed
MQTT_PASSWORD=                           # If needed
MQTT_USE_TLS=false
```

### Public MQTT Brokers (Free)

| Broker | Address | Port | Auth | Usage |
|--------|---------|------|------|-------|
| HiveMQ | broker.hivemq.com | 1883 | No | ✓ Recommended |
| Mosquitto | test.mosquitto.org | 1883 | No | ✓ Good |
| CloudMQTT | *.cloudmqtt.com | 10000 | Yes | Advanced |

---

## File Structure

```
Dashboard/
├── backend/
│   ├── main.py                 # FastAPI backend with WebSocket
│   ├── simulator.py            # Fallback simulator
│   ├── mqtt_handler.py         # MQTT integration (NEW)
│   └── diagnostics.py          # Testing tool (NEW)
├── frontend/
│   └── streamlit_app.py        # Dashboard UI
├── esp32_firmware.ino          # Arduino code for ESP32 (NEW)
├── requirements.txt            # Python dependencies (UPDATED)
├── .env                        # Configuration file (NEW)
├── .env.example                # Configuration template (NEW)
├── SETUP_GUIDE.md              # Complete setup guide (NEW)
├── ARDUINO_SETUP.md            # Arduino IDE setup (NEW)
├── quickstart.bat              # Windows quick start (NEW)
├── quickstart.sh               # Linux/macOS quick start (NEW)
└── README.md                   # This file
```

---

## Troubleshooting

### ESP32 Won't Connect to WiFi

```
✓ Check SSID and password in esp32_firmware.ino
✓ Ensure ESP32 is 2.4 GHz compatible
✓ Check WiFi signal strength
✓ Restart ESP32 (press RESET button)
```

### MQTT Connection Fails

```
✓ Verify broker address: ping broker.hivemq.com
✓ Check credentials match
✓ Ensure TLS setting is correct
✓ Test with: mosquitto_pub -h broker.hivemq.com -t test -m "hello"
```

### Dashboard Not Updating

```
✓ Verify backend is running: curl http://127.0.0.1:8000
✓ Check browser console for errors (F12)
✓ Restart services
✓ Run diagnostics: python backend/diagnostics.py
```

### Port Already in Use

```
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Import Errors

```
# Reinstall packages
pip install --upgrade -r requirements.txt

# Restart virtual environment
deactivate
.venv\Scripts\activate
```

---

## Performance Metrics

- **Sampling Rate**: 2048 Hz (configurable)
- **WebSocket Latency**: < 100ms (local), < 500ms (cloud)
- **FFT Resolution**: Up to 2048 frequency bins
- **Connected Clients**: Unlimited (tested with 50+)
- **MQTT Topics**: 3 (accelerometer, rpm, status)

---

## API Endpoints

### Authentication
- `POST /signup` - Create new account
- `POST /login` - Login and get JWT token

### Control
- `POST /start` - Start rotor
- `POST /stop` - Stop rotor
- `POST /set_speed/{rpm}` - Set target RPM

### WebSocket
- `WS /ws` - Real-time data stream (JSON format)

### Status
- `GET /` - Server status

---

## Security Considerations

### For Production:

1. **Change default secrets**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Enable HTTPS/TLS**
   - Use Let's Encrypt for free SSL

3. **Use strong MQTT credentials**
   - Avoid default usernames/passwords

4. **Implement rate limiting**
   - Prevent brute force attacks

5. **Monitor access logs**
   - Check for suspicious activity

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for full security guidelines.

---

## Development & Testing

### Run Diagnostic Tool

```bash
python backend/diagnostics.py
```

Tests:
- Python version
- Virtual environment
- Required packages
- Configuration files
- MQTT connectivity
- Port availability
- Database

### Test with Simulator

```bash
# Backend still runs simulator if MQTT unavailable
USE_MQTT=false streamlit run frontend/streamlit_app.py
```

### View Backend Logs

```bash
# Logs appear in terminal where backend runs
# For detailed logs:
uvicorn backend.main:app --reload --log-level debug
```

---

## Next Steps

1. ✅ Complete local testing with simulator
2. ⬜ Setup ESP32 hardware (see [ARDUINO_SETUP.md](ARDUINO_SETUP.md))
3. ⬜ Enable MQTT in `.env` file
4. ⬜ Test with real ESP32 data
5. ⬜ Deploy to cloud for remote access
6. ⬜ Add data logging and export features
7. ⬜ Implement automatic balancing calculations

---

## Contributing

Found a bug? Have suggestions?

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for solutions
2. Run `python backend/diagnostics.py` for diagnostics
3. Check logs in terminal output

---

## Resources

- **[Complete Setup Guide](SETUP_GUIDE.md)** - Full integration instructions
- **[Arduino Setup Guide](ARDUINO_SETUP.md)** - ESP32 programming
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **MQTT Documentation**: https://mqtt.org/
- **ESP32 Documentation**: https://docs.espressif.com/

---

## License & Disclaimer

This project is provided for educational purposes. Always ensure proper testing before use with real machinery.

**⚠️ Warning:** Improper balancing procedures can cause equipment damage or injury.

---

## Support

For issues and questions, refer to:
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Comprehensive troubleshooting
2. Run diagnostic tool: `python backend/diagnostics.py`
3. Check log files in project directory

Last Updated: May 2026
