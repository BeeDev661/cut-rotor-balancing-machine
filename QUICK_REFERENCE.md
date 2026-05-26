# Quick Reference Card - ESP32 Dashboard Setup

## 🚀 Start Here (Choose One)

### Option 1: Windows Users (Easiest)
```bash
cd c:\Users\acer\Desktop\Dashboard
quickstart.bat
# Follow prompts - done in 60 seconds!
```

### Option 2: macOS/Linux Users
```bash
cd ~/Desktop/Dashboard
chmod +x quickstart.sh
./quickstart.sh
# Follow prompts - done in 60 seconds!
```

### Option 3: Manual Setup
```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Terminal 1 - Start backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 3. Terminal 2 - Start dashboard
streamlit run frontend/streamlit_app.py

# 4. Browser
# http://localhost:8501
```

---

## 🛠️ Configuration Quick Guide

### File: `.env`

```bash
# For SIMULATOR TESTING (No hardware needed)
USE_MQTT=false

# For ESP32 + PUBLIC BROKER (Recommended)
USE_MQTT=true
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_USER=
MQTT_PASSWORD=

# For Self-Hosted MQTT
USE_MQTT=true
MQTT_BROKER=your-server.com
MQTT_PORT=1883
MQTT_USER=esp32_user
MQTT_PASSWORD=your_password
```

---

## 📱 ESP32 Firmware Quick Start

### Step 1: Install Arduino IDE
- Download from https://www.arduino.cc/en/software
- See ARDUINO_SETUP.md for detailed instructions

### Step 2: Install Libraries (Arduino > Sketch > Include Library > Manage Libraries)
- Search & install: **MPU6050** by Jeff Rowberg
- Search & install: **PubSubClient** by Nick O'Leary  
- Search & install: **ArduinoJson** by Benoit Blanchon

### Step 3: Upload Firmware
1. Open `esp32_firmware.ino`
2. Modify WiFi settings:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "broker.hivemq.com";
   ```
3. Connect ESP32 via USB
4. Click **Upload** button
5. Check Serial Monitor (115200 baud) for "MQTT connected"

---

## 🔌 Hardware Connections

```
MPU6050 Accelerometer:
- VCC     → ESP32 3.3V
- GND     → ESP32 GND  
- SDA     → ESP32 GPIO 21
- SCL     → ESP32 GPIO 22

Hall Sensor (Optional RPM):
- GND     → ESP32 GND
- VCC     → ESP32 3.3V
- OUT     → ESP32 GPIO 35
```

---

## 📊 Dashboard Features

Once running, you can:
- ✅ **Sign Up/Login** - Create user account
- ✅ **View Real-Time Data** - RPM, acceleration, FFT
- ✅ **Control Machine** - Start/Stop/Set Speed
- ✅ **See Graphs** - Time-domain & frequency-domain
- ✅ **Get Recommendations** - Balancing mass placement

---

## 🌐 Go Online (Cloud Deployment)

### Option 1: Heroku (Easiest)
```bash
# 1. Create account at heroku.com
# 2. Install Heroku CLI
# 3. Run:
heroku login
heroku create your-app-name
git push heroku main
# Your backend: https://your-app-name.herokuapp.com
```

### Option 2: AWS / DigitalOcean
- See SETUP_GUIDE.md for detailed steps
- Takes ~30 minutes

### Option 3: Streamlit Cloud (Dashboard only)
- Push to GitHub
- Deploy from https://streamlit.io/cloud
- Takes ~5 minutes

---

## 🧪 Test Your Setup

```bash
# Run diagnostic tool
python backend/diagnostics.py

# Checks:
✓ Python version
✓ Virtual environment
✓ Required packages
✓ Configuration files
✓ MQTT broker connectivity
✓ Port availability
✓ Database
```

---

## 🔧 Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `taskkill /PID <PID> /F` (Windows) or `kill -9 <PID>` (Mac/Linux) |
| MQTT connection fails | Check broker address in .env |
| ESP32 won't upload | Try different USB cable or port |
| Dashboard not updating | Verify backend running: `curl http://127.0.0.1:8000` |
| MPU6050 not found | Check I2C connections or run I2C scanner sketch |
| Import errors | `pip install --upgrade -r requirements.txt` |

See SETUP_GUIDE.md for 20+ more solutions!

---

## 📁 Important Files

| File | Purpose | Edit? |
|------|---------|-------|
| `.env` | Configuration | ✏️ Yes - set MQTT broker |
| `esp32_firmware.ino` | ESP32 code | ✏️ Yes - set WiFi/MQTT |
| `backend/main.py` | Backend logic | ⚠️ Only if advanced |
| `requirements.txt` | Dependencies | ⚠️ Only if adding packages |

---

## 📞 Getting Help

1. **Quick Answers**: IMPLEMENTATION_SUMMARY.md
2. **Setup Issues**: SETUP_GUIDE.md (70+ sections)
3. **Arduino Issues**: ARDUINO_SETUP.md
4. **Run Diagnostics**: `python backend/diagnostics.py`

---

## ✅ Completion Checklist

- [ ] Downloaded and extracted project
- [ ] Ran quickstart script
- [ ] Tested simulator mode (saw graphs update)
- [ ] Signed up for account in dashboard
- [ ] Installed Arduino IDE
- [ ] Uploaded esp32_firmware.ino to ESP32
- [ ] ESP32 connected to WiFi (saw in Serial Monitor)
- [ ] Enabled MQTT in .env file
- [ ] Saw real ESP32 data in dashboard
- [ ] Deployed to cloud (optional)
- [ ] Accessed dashboard from phone/other device

---

## 🎯 You're Ready!

Your dashboard can now:
1. **Collect** real-time ESP32 sensor data
2. **Display** live FFT and vibration analysis
3. **Control** your rotor machine remotely
4. **Share** with team members online

**Estimated Time**: 2-3 hours from zero to full deployment

---

## 📚 Next Steps

1. **Immediate**: Run quickstart.bat and explore
2. **This Week**: Set up ESP32 hardware
3. **This Month**: Deploy to cloud
4. **Future**: Add data logging, alerts, ML analysis

**Questions?** Check the 4 guide documents - they cover everything!

---

**Dashboard Version**: 2.0 with ESP32 Support ✅
**Last Updated**: May 2026
**Status**: Production Ready 🚀
