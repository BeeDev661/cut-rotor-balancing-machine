# ESP32 Rotor Balancing Dashboard - Complete Setup Guide

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Setup ESP32 Hardware](#setup-esp32-hardware)
4. [Local Setup (Testing)](#local-setup-testing)
5. [Cloud Deployment (Remote Access)](#cloud-deployment-remote-access)
6. [Troubleshooting](#troubleshooting)

---

## System Architecture

```
┌─────────────┐
│ ESP32 Board │  (WiFi)
├─────────────┤
│ MPU6050     │ ──┐
│ Hall Sensor │   │  MQTT
└─────────────┘   │
                  │
                  ▼
            ┌──────────────┐
            │ MQTT Broker  │ (Cloud or Local)
            └──────────────┘
                  ▲
                  │ MQTT Subscribe
                  │
            ┌──────────────────────┐
            │  FastAPI Backend     │ (Port 8000)
            │  (mqtt_handler.py)   │
            └──────────────────────┘
                  ▲
                  │ WebSocket
                  │
            ┌──────────────────────┐
            │ Streamlit Dashboard  │ (Port 8501)
            │ (Web Browser)        │
            └──────────────────────┘
```

---

## Prerequisites

### For ESP32 Setup:
- ESP32 Development Board (e.g., ESP32-WROOM-32)
- MPU6050 Accelerometer/Gyroscope
- Hall Effect Sensor (for RPM measurement) - Optional
- USB Cable for programming
- Arduino IDE with ESP32 support

### For Backend:
- Python 3.9+
- pip (Python package manager)

### For Remote Access:
- Public MQTT Broker (free options: HiveMQ, test.mosquitto.org, or CloudMQTT)
- Domain name or Static IP (optional, for direct access)
- Internet connection on both ESP32 and server

---

## Setup ESP32 Hardware

### 1. Install Arduino IDE & ESP32 Support

```bash
# Download Arduino IDE from https://www.arduino.cc/en/software
# Or use VS Code with PlatformIO extension
```

### 2. Install Required Libraries in Arduino IDE

Go to **Sketch > Include Library > Manage Libraries** and install:
- `MPU6050` by Jeff Rowberg (search: "MPU6050")
- `PubSubClient` by Nick O'Leary (for MQTT)
- `ArduinoJson` by Benoit Blanchon (for JSON serialization)

### 3. Hardware Connections

```
MPU6050 Connections:
├─ VCC → ESP32 3.3V
├─ GND → ESP32 GND
├─ SDA → ESP32 GPIO 21
├─ SCL → ESP32 GPIO 22
└─ INT → GPIO 35 (optional for interrupt mode)

Hall Sensor Connections (Optional for RPM):
├─ GND → ESP32 GND
├─ VCC → ESP32 3.3V (via voltage regulator if 5V sensor)
└─ OUT → ESP32 GPIO 35 (or any GPIO with interrupt capability)
```

### 4. Upload ESP32 Firmware

1. Open `esp32_firmware.ino` in Arduino IDE
2. Modify these lines with your WiFi and MQTT details:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "mqtt.example.com";
   const char* mqtt_user = "esp32_user";
   const char* mqtt_password = "esp32_password";
   ```

3. Select Board: **Tools > Board > ESP32 > ESP32 Dev Module**
4. Select Port: **Tools > Port > COM_PORT**
5. Click **Upload** button

6. Open Serial Monitor (**Tools > Serial Monitor**, 115200 baud) to verify:
   ```
   ESP32 Rotor Balancing Sensor Initialized
   MPU6050 initialized successfully
   Connecting to WiFi: YOUR_WIFI_SSID
   WiFi connected
   IP address: 192.168.x.x
   Attempting MQTT connection...
   MQTT connected
   ```

---

## Local Setup (Testing)

### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd c:\Users\acer\Desktop\Dashboard

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
# source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Set Up Local MQTT Broker (Optional for local testing)

#### Option A: Using Mosquitto (Free)

**Windows:**
```bash
# Install using Chocolatey
choco install mosquitto

# Or download from: https://mosquitto.org/download/
```

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

#### Option B: Skip Local Broker (Use Public One)

We'll use a public free broker in the next step.

### Step 3: Configure Backend (.env file)

Edit `.env` file in the project root:

**For Testing with Public MQTT Broker (Recommended):**

```bash
# Use HiveMQ (free, no authentication)
USE_MQTT=false
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_USER=
MQTT_PASSWORD=
MQTT_USE_TLS=false
```

**For Testing with Local Simulator:**
```bash
USE_MQTT=false
```

### Step 4: Start Backend

```bash
# Terminal 1 (from project root with .venv activated)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 5: Start Dashboard

```bash
# Terminal 2 (from project root with .venv activated)
streamlit run frontend/streamlit_app.py
```

Dashboard opens at: **http://localhost:8501**

### Step 6: Test Dashboard

1. Sign up with a test account (username: `test`, password: `test123`)
2. Click **Start** button to begin simulator
3. Adjust RPM slider and click **Apply Speed**
4. Verify FFT and time-domain plots update in real-time

---

## Cloud Deployment (Remote Access)

### Phase 1: Switch to Public MQTT Broker

#### Option 1: HiveMQ (Easiest - No Auth)

Edit `.env`:
```bash
USE_MQTT=true
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_USER=
MQTT_PASSWORD=
MQTT_USE_TLS=false
```

#### Option 2: CloudMQTT (More Reliable)

1. Create free account at https://www.cloudmqtt.com/
2. Create new instance (free tier)
3. Get credentials from dashboard:
   - Server: `instance.cloudmqtt.com`
   - Port: `10000` or `1883`
   - User: `username`
   - Password: `password`

Edit `.env`:
```bash
USE_MQTT=true
MQTT_BROKER=your_instance.cloudmqtt.com
MQTT_PORT=10000
MQTT_USER=your_username
MQTT_PASSWORD=your_password
MQTT_USE_TLS=true
```

#### Option 3: Mosquitto (Self-hosted on a VPS)

For advanced users: Deploy Mosquitto on a cloud VPS (AWS, DigitalOcean, etc.)

### Phase 2: Deploy Backend Online

#### Option A: Using Heroku (Easiest)

1. Create account at https://heroku.com/
2. Install Heroku CLI
3. Create `Procfile` in project root:
   ```
   web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

4. Deploy:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

5. Get URL: `https://your-app-name.herokuapp.com`

#### Option B: Using AWS EC2 (More Control)

1. Launch EC2 instance (Ubuntu 20.04)
2. SSH into instance
3. Install Python and dependencies
4. Clone your repository
5. Start backend with PM2 or supervisor:
   ```bash
   npm install -g pm2
   pm2 start "uvicorn backend.main:app --host 0.0.0.0 --port 8000"
   ```

6. Get IP address and use for connection

#### Option C: Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to Docker Hub or AWS ECR

### Phase 3: Update ESP32 Firmware for Remote Access

Modify `esp32_firmware.ino`:
```cpp
// Change from localhost to your broker
const char* mqtt_server = "broker.hivemq.com";  // or your CloudMQTT instance
const int mqtt_port = 1883;
const char* mqtt_user = "";  // if using HiveMQ
const char* mqtt_password = "";
```

Reupload firmware to ESP32

### Phase 4: Deploy Dashboard (Streamlit Cloud)

1. Push code to GitHub: https://github.com
2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `frontend/streamlit_app.py`
6. Deploy

Add secrets in Streamlit Cloud settings:
```
DASHBOARD_API_URL=https://your-backend-url.com
DASHBOARD_SECRET=your_secure_secret_key
```

Alternatively, modify frontend connection in `streamlit_app.py`:
```python
# Find this section and modify:
env_api = os.getenv("DASHBOARD_API_URL", "https://your-backend.herokuapp.com")
```

---

## Remote Monitoring Workflow

### To Monitor from Anywhere:

1. **Access Dashboard:** Open the deployed Streamlit app URL (e.g., `https://your-app.streamlit.app`)
2. **Sign In:** Use your credentials
3. **View Live Data:** Real-time FFT, RPM, and accelerometer data from ESP32
4. **Control Machine:** Start/Stop and adjust speed remotely
5. **Download Data:** Add export feature to CSV (optional enhancement)

---

## Security Considerations

### For Production Deployment:

1. **Change default credentials:**
   ```bash
   # Generate strong secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Enable HTTPS/TLS:**
   - Use Let's Encrypt for free SSL certificates
   - Update `.env` with MQTT_USE_TLS=true

3. **Protect API endpoints:**
   - Add rate limiting
   - Implement IP whitelisting
   - Use strong JWT tokens

4. **Monitor MQTT traffic:**
   - Use authenticated brokers
   - Consider VPN for additional security

5. **Firewall rules:**
   - Only expose WebSocket and HTTP ports
   - Block direct MQTT port (1883) access from internet

---

## Troubleshooting

### ESP32 Issues

**Problem: ESP32 won't upload firmware**
```
Solution:
1. Check USB cable is connected properly
2. Select correct COM port in Arduino IDE
3. Try different USB port
4. Install CH340 drivers if using cheap clones
```

**Problem: WiFi connection fails**
```
Solution:
1. Verify SSID and password in code
2. Check WiFi signal strength (move router closer)
3. Ensure ESP32 supports your WiFi band (2.4 GHz)
4. Check if network uses WPA3 (may not be supported)
```

**Problem: MQTT connection fails**
```
Solution:
1. Verify MQTT broker address is correct
2. Check credentials (username/password)
3. Ensure TLS setting matches broker configuration
4. Test broker connectivity from desktop:
   mosquitto_pub -h broker.hivemq.com -t test -m "hello"
```

**Problem: No sensor data received**
```
Solution:
1. Check MPU6050 connections (SDA=GPIO21, SCL=GPIO22)
2. Scan I2C devices: Use I2C scanner sketch
3. Verify MPU6050 address (usually 0x68)
4. Check if sensor has pull-up resistors (4.7kΩ on SDA/SCL)
```

### Backend Issues

**Problem: MQTT connection fails from backend**
```
Solution:
1. Verify .env file is in project root
2. Test MQTT broker connection:
   python -c "import paho.mqtt.client; client = paho.mqtt.client.Client(); client.connect('broker.hivemq.com')"
3. Check firewall isn't blocking MQTT port
4. Try with different public broker
```

**Problem: WebSocket connection hangs**
```
Solution:
1. Check backend is running: http://127.0.0.1:8000
2. Verify dashboard connects to correct API_URL
3. Check firewall/router isn't blocking port 8000
4. Look for errors in backend console
```

**Problem: Dashboard not receiving data**
```
Solution:
1. Verify backend is streaming data (check console)
2. Ensure MQTT topics match:
   - esp32/accelerometer
   - esp32/rpm
3. Check simulator is set to running if not using MQTT
4. Verify authentication token is valid
```

### Deployment Issues

**Problem: Remote access doesn't work**
```
Solution:
1. Test backend is publicly accessible:
   curl https://your-backend.com/
2. Check firewall allows incoming connections
3. Verify DNS is resolving correctly
4. Check backend logs for errors
5. Ensure ESP32 can reach MQTT broker address
```

**Problem: High latency or lag**
```
Solution:
1. Reduce WebSocket message frequency
2. Use local MQTT broker instead of cloud broker
3. Check internet speed on both ends
4. Consider deploying backend closer to ESP32
```

---

## Testing Checklist

- [ ] ESP32 connects to WiFi
- [ ] ESP32 publishes to MQTT broker
- [ ] Backend receives MQTT messages
- [ ] Dashboard displays real-time data
- [ ] Start/Stop button works
- [ ] RPM adjustment works
- [ ] User authentication works
- [ ] Remote access possible
- [ ] Data persists across reconnections
- [ ] FFT calculations are correct

---

## Next Steps

1. **Data Logging:** Store sensor data to database
2. **Alerts:** Send notifications for abnormal vibrations
3. **Historical Analysis:** View past performance reports
4. **Mobile App:** Create native iOS/Android app
5. **Machine Learning:** Detect imbalance patterns automatically
6. **Balancing Calculations:** Add automatic mass placement recommendations

---

## Support & Resources

- ESP32 Documentation: https://docs.espressif.com/projects/esp-idf/
- MQTT Documentation: https://mqtt.org/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/
- Public MQTT Brokers: https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

---

## License & Disclaimer

This project is provided as-is for educational purposes. Ensure proper testing before use with real machinery. Improper balancing procedures can cause equipment damage or injury.
