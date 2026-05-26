# ESP32 Arduino Setup Guide

## Installing Arduino IDE

### Windows

1. Download from https://www.arduino.cc/en/software
2. Run installer and follow prompts
3. Launch Arduino IDE

### macOS

```bash
# Using Homebrew (recommended)
brew install arduino-ide

# Or download from https://www.arduino.cc/en/software
```

### Linux (Ubuntu/Debian)

```bash
# Using snap
sudo snap install arduino

# Or download from https://www.arduino.cc/en/software
```

---

## Adding ESP32 Support to Arduino IDE

### Method 1: Using Board Manager (Recommended)

1. Open Arduino IDE
2. Go to **File > Preferences**
3. In "Additional Boards Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click OK
5. Go to **Tools > Board > Boards Manager**
6. Search for "ESP32"
7. Install "esp32" by Espressif Systems
8. Wait for installation to complete (~2 minutes)

### Method 2: Using PlatformIO (VS Code)

1. Install VS Code from https://code.visualstudio.com/
2. Install "PlatformIO IDE" extension from VS Code marketplace
3. Create new project: **PlatformIO > New Project**
4. Select board: "Espressif ESP32 Dev Module"
5. PlatformIO handles everything automatically

---

## Installing Required Libraries

### Using Arduino IDE Library Manager

1. Open Arduino IDE
2. Go to **Sketch > Include Library > Manage Libraries**
3. Search and install each:

#### Library 1: MPU6050

```
Search: "MPU6050"
Install: "MPU6050" by Jeff Rowberg
Version: Latest
```

#### Library 2: PubSubClient (MQTT)

```
Search: "PubSubClient"
Install: "PubSubClient" by Nick O'Leary
Version: Latest (2.8 or higher)
```

#### Library 3: ArduinoJson

```
Search: "ArduinoJson"
Install: "ArduinoJson" by Benoit Blanchon
Version: 6.x (not 7.x)
```

---

## Verifying Installation

1. Open Arduino IDE
2. Go to **Tools > Board** and verify "ESP32 Dev Module" is available
3. Create new sketch: **File > New**
4. Include the libraries:
   ```cpp
   #include <Wire.h>
   #include <MPU6050.h>
   #include <PubSubClient.h>
   #include <ArduinoJson.h>
   #include <WiFi.h>
   ```
5. Click **Verify** button (checkmark icon)
6. If no errors appear, installation is successful!

---

## Selecting Board and Port

### Select Board
1. **Tools > Board > ESP32 Arduino > ESP32 Dev Module**

### Select Port
1. Connect ESP32 via USB
2. **Tools > Port > COM?** (Windows)
   - Or **/dev/ttyUSB0** (Linux)
   - Or **/dev/cu.usbserial-** (macOS)

### If Port Doesn't Appear

**Windows:**
- Install CH340 drivers: https://github.com/WCHSoftware/ch341ser
- Right-click installer and select "Run as Administrator"
- Restart computer

**macOS:**
```bash
# Install via Homebrew
brew install wch-ch34x-usb-serial-driver

# Restart system
```

**Linux:**
```bash
# CH340 drivers usually work automatically
# If not, install:
sudo apt-get install ch340g

# Then reconnect device
```

---

## Uploading Code

1. Open `esp32_firmware.ino`
2. Modify WiFi and MQTT settings at the top:
   ```cpp
   const char* ssid = "YOUR_SSID";
   const char* password = "YOUR_PASSWORD";
   const char* mqtt_server = "broker.hivemq.com";
   ```
3. Click **Upload** button (arrow icon)
4. Wait for upload to complete (~30 seconds)
5. Open **Tools > Serial Monitor** (speed: 115200)
6. Watch for startup messages

---

## Troubleshooting Installation

### "Board not found" in Port menu

```
Solution:
1. Verify USB cable is connected
2. Try different USB port
3. Check if device appears in:
   - Windows: Device Manager
   - macOS: System Information > USB
   - Linux: lsusb command
4. Install CH340 drivers (see above)
```

### "Compilation error" when uploading

```
Solution:
1. Verify all libraries are installed
2. Check board selection: Tools > Board > ESP32 Dev Module
3. Try re-installing libraries
4. Close other instances of Arduino IDE
```

### "TIMEOUT" during upload

```
Solution:
1. Try different USB cable
2. Press and hold BOOT button while uploading
3. Try uploading at slower baud rate:
   Tools > Upload Speed > 115200
4. Install latest CH340 drivers
```

### Libraries not found in code

```
Solution:
1. Verify library installation in Library Manager
2. Close and reopen Arduino IDE
3. Make sure #include statements match exactly:
   #include <MPU6050.h>
   (not #include "MPU6050.h")
```

---

## Testing ESP32 Connection

### Test 1: Serial Output
```cpp
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 is working!");
}

void loop() {
  delay(1000);
}
```

### Test 2: I2C Scan (Find MPU6050)
```cpp
#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);  // SDA=21, SCL=22
  Serial.println("I2C Scanner");
}

void loop() {
  for (byte i = 8; i < 120; i++) {
    Wire.beginTransmission(i);
    if (Wire.endTransmission() == 0) {
      Serial.print("Device found at address 0x");
      Serial.println(i, HEX);
    }
  }
  delay(5000);
}
```

### Test 3: WiFi Connection
```cpp
#include <WiFi.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  WiFi.begin(ssid, password);
  int count = 0;
  
  while (WiFi.status() != WL_CONNECTED && count < 20) {
    delay(500);
    Serial.print(".");
    count++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect");
  }
}

void loop() {}
```

---

## Next: Upload Main Firmware

Once verified:
1. Copy content of `esp32_firmware.ino`
2. Paste into Arduino IDE
3. Modify WiFi and MQTT settings
4. Upload to ESP32

Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for next steps!
