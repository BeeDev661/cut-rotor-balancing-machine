/*
  ESP32 Rotor Balancing Dashboard Sensor Integration
  
  Hardware Required:
  - ESP32 Development Board
  - MPU6050 Accelerometer/Gyroscope (I2C address: 0x68)
  - DC Motor with Hall sensor for RPM (optional, or use PWM simulation)
  
  Connections:
  - MPU6050 SDA → GPIO 21 (SDA)
  - MPU6050 SCL → GPIO 22 (SCL)
  - Hall Sensor → GPIO 35 (Input, with pull-up)
  
  Configuration:
  - WiFi SSID and password in WiFi_Settings section
  - MQTT broker address, port, username, password
  - Device calibration parameters
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <MPU6050.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <time.h>

// ============ WiFi Settings ============
const char* ssid = "YOUR_WIFI_SSID";           // Change this
const char* password = "YOUR_WIFI_PASSWORD";   // Change this

// ============ MQTT Settings ============
const char* mqtt_server = "mqtt.example.com";  // Public MQTT broker or your IP
const int mqtt_port = 1883;                    // 8883 for TLS
const char* mqtt_user = "esp32_user";          // Change this
const char* mqtt_password = "esp32_password";  // Change this
const char* mqtt_client_id = "esp32_rotor_sensor";

// ============ Topics ============
const char* topic_accelerometer = "esp32/accelerometer";
const char* topic_rpm = "esp32/rpm";
const char* topic_status = "esp32/status";

// ============ Timing & Configuration ============
const int SAMPLE_RATE = 2048;                  // Hz (2048 samples/sec)
const int SAMPLES_PER_CHUNK = 512;             // Send 512 samples per transmission (~250ms)
const int PUBLISH_INTERVAL = 250;              // ms between MQTT publishes
const int HALL_SENSOR_PIN = 35;                // GPIO pin for Hall sensor

// ============ Global Variables ============
WiFiClient espClient;
PubSubClient mqtt_client(espClient);
MPU6050 mpu;

float accel_x, accel_y, accel_z;
float gyro_x, gyro_y, gyro_z;
float rpm = 0.0;
int hall_pulses = 0;
int last_hall_pulses = 0;

unsigned long last_publish_time = 0;
unsigned long last_rpm_calc_time = 0;
unsigned long sample_count = 0;

// Ring buffer for accelerometer samples
float acc_buffer[SAMPLES_PER_CHUNK] = {0};
int buffer_index = 0;

// Calibration (adjust based on your MPU6050)
float accel_scale = 9.81 / 16384.0;  // ±2g range, LSB = 16384
float gyro_scale = 1.0 / 131.0;      // ±250°/s range


// ============ Function Declarations ============
void setup_wifi();
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void reconnect_mqtt();
void publish_sensor_data();
void update_rpm();
void IRAM_ATTR hall_sensor_isr();
void read_mpu6050();


// ============ Setup ============
void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n\nESP32 Rotor Balancing Sensor Initialized");
  Serial.println("Version: 1.0");
  
  // Initialize I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22
  
  // Initialize MPU6050
  if (!mpu.begin(MPU6050_SCALE_2000DPS, MPU6050_RANGE_2G)) {
    Serial.println("MPU6050 connection failed!");
    while (1);
  }
  
  mpu.setAccelOffsetX(0);
  mpu.setAccelOffsetY(0);
  mpu.setAccelOffsetZ(0);
  
  Serial.println("MPU6050 initialized successfully");
  
  // Initialize Hall sensor
  pinMode(HALL_SENSOR_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(HALL_SENSOR_PIN), hall_sensor_isr, RISING);
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  mqtt_client.setServer(mqtt_server, mqtt_port);
  mqtt_client.setCallback(mqtt_callback);
  
  Serial.println("Setup completed");
}


// ============ Main Loop ============
void loop() {
  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }
  
  // Maintain MQTT connection
  if (!mqtt_client.connected()) {
    reconnect_mqtt();
  }
  mqtt_client.loop();
  
  // Read sensor data
  read_mpu6050();
  
  // Accumulate acceleration magnitude as single value
  // (You can modify this to send raw acc_x, acc_y, acc_z instead)
  float acc_magnitude = sqrt(accel_x * accel_x + accel_y * accel_y + accel_z * accel_z);
  acc_buffer[buffer_index] = acc_magnitude;
  buffer_index++;
  sample_count++;
  
  // Calculate RPM every 1 second
  unsigned long current_time = millis();
  if (current_time - last_rpm_calc_time >= 1000) {
    update_rpm();
    last_rpm_calc_time = current_time;
  }
  
  // Publish data at specified interval
  if (current_time - last_publish_time >= PUBLISH_INTERVAL && buffer_index >= SAMPLES_PER_CHUNK) {
    publish_sensor_data();
    last_publish_time = current_time;
    buffer_index = 0;  // Reset buffer
  }
  
  // Sampling delay (to maintain ~2048 Hz sampling rate)
  // 1000000 microseconds / 2048 samples = ~488 microseconds per sample
  delayMicroseconds(488);
}


// ============ WiFi Setup ============
void setup_wifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}


// ============ MQTT Callback ============
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.println(topic);
  
  // Handle incoming commands if needed
  if (strcmp(topic, "esp32/command") == 0) {
    String command = "";
    for (int i = 0; i < length; i++) {
      command += (char)payload[i];
    }
    Serial.print("Command: ");
    Serial.println(command);
    
    // Example: handle calibration command
    if (command == "calibrate") {
      Serial.println("Calibrating sensors...");
    }
  }
}


// ============ MQTT Reconnect ============
void reconnect_mqtt() {
  if (!mqtt_client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (mqtt_client.connect(mqtt_client_id, mqtt_user, mqtt_password)) {
      Serial.println("MQTT connected");
      
      // Publish online status
      StaticJsonDocument<256> status_doc;
      status_doc["status"] = "online";
      status_doc["ip_address"] = WiFi.localIP().toString();
      status_doc["sample_rate"] = SAMPLE_RATE;
      
      char status_buffer[256];
      serializeJson(status_doc, status_buffer);
      mqtt_client.publish(topic_status, status_buffer);
      
      // Subscribe to commands
      mqtt_client.subscribe("esp32/command");
    } else {
      Serial.print("MQTT connection failed, rc=");
      Serial.println(mqtt_client.state());
    }
  }
}


// ============ Publish Sensor Data ============
void publish_sensor_data() {
  // Create JSON document for accelerometer data
  StaticJsonDocument<2048> accel_doc;
  
  // Convert accelerometer samples to array
  JsonArray acc_array = accel_doc.createNestedArray("acc");
  for (int i = 0; i < SAMPLES_PER_CHUNK; i++) {
    acc_array.add(acc_buffer[i]);
  }
  
  accel_doc["sample_rate"] = SAMPLE_RATE;
  accel_doc["timestamp"] = (long)time(nullptr);
  accel_doc["sample_count"] = sample_count;
  
  // Publish accelerometer data
  char accel_buffer_str[2048];
  size_t n = serializeJson(accel_doc, accel_buffer_str);
  
  if (mqtt_client.publish(topic_accelerometer, accel_buffer_str, n)) {
    Serial.printf("Published accelerometer: %d samples, timestamp: %lu\n", 
                  SAMPLES_PER_CHUNK, (long)time(nullptr));
  } else {
    Serial.println("Failed to publish accelerometer data");
  }
  
  // Create JSON document for RPM data
  StaticJsonDocument<256> rpm_doc;
  rpm_doc["rpm"] = rpm;
  rpm_doc["timestamp"] = (long)time(nullptr);
  
  // Publish RPM data
  char rpm_buffer[256];
  serializeJson(rpm_doc, rpm_buffer);
  
  if (mqtt_client.publish(topic_rpm, rpm_buffer)) {
    Serial.printf("Published RPM: %.2f\n", rpm);
  } else {
    Serial.println("Failed to publish RPM data");
  }
}


// ============ Update RPM ============
void update_rpm() {
  // Calculate RPM from Hall sensor pulses
  // Assuming: 1 pulse per rotor revolution
  int pulses_since_last = hall_pulses - last_hall_pulses;
  last_hall_pulses = hall_pulses;
  
  // RPM = (pulses / pulses_per_revolution) * 60 / time_seconds
  // For 1 pulse per revolution over 1 second:
  rpm = (float)pulses_since_last * 60.0;
  
  Serial.printf("RPM: %.2f (Hall pulses: %d)\n", rpm, hall_pulses);
}


// ============ Read MPU6050 ============
void read_mpu6050() {
  Vector rawAccel = mpu.readRawAccel();
  Vector rawGyro = mpu.readRawGyro();
  
  // Convert to physical units
  accel_x = rawAccel.XAxis * accel_scale;
  accel_y = rawAccel.YAxis * accel_scale;
  accel_z = rawAccel.ZAxis * accel_scale;
  
  gyro_x = rawGyro.XAxis * gyro_scale;
  gyro_y = rawGyro.YAxis * gyro_scale;
  gyro_z = rawGyro.ZAxis * gyro_scale;
}


// ============ Hall Sensor ISR ============
void IRAM_ATTR hall_sensor_isr() {
  hall_pulses++;
}
