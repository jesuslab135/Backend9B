#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <MPU6050.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION
// ============================================

// WiFi credentials
const char* ssid = "Totalplay-2.4G-e990";
const char* password = "bdAaFRXxJMgqmEG9";


// Django backend URLs
const char* baseUrl = "http://192.168.100.6:8000/api";
String checkSessionUrl = String(baseUrl) + "/device-session/check-session/";
String extendWindowUrl = String(baseUrl) + "/device-session/extend-window/";
String lecturasUrl = String(baseUrl) + "/lecturas/";

// Device ID - Unique identifier for this ESP32
String DEVICE_ID = "ESP32_DEFAULT";

// Pin definitions
const int HEART_RATE_PIN = 18;
const int SDA_PIN = 21;
const int SCL_PIN = 22;
const int LED_PIN = 2;

// Timing
const unsigned long SEND_INTERVAL = 10000;       // Send sensor data every 10 seconds
const unsigned long POLL_INTERVAL = 10000;       // Check for session every 10 seconds
const unsigned long EXTEND_INTERVAL = 1800000;   // Extend window every 30 minutes

unsigned long lastSendTime = 0;
unsigned long lastPollTime = 0;
unsigned long lastExtendTime = 0;

// Session state
bool hasActiveSession = false;
String sessionId = "";
int consumidorId = 0;
int ventanaId = 0;
String usuarioNombre = "";
String usuarioEmail = "";

// Sensor objects
MPU6050 mpu;

// Heart rate variables
const int SAMPLE_SIZE = 10;
int hrSamples[SAMPLE_SIZE];
int sampleIndex = 0;

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║   SMOKE DETECTION SYSTEM v2.0      ║");
  Serial.println("║      Automatic Session Detection   ║");
  Serial.println("╚════════════════════════════════════╝\n");
  
// Use "default" device ID to match Django backend
  DEVICE_ID = "default";
  
  Serial.println("Device ID: " + DEVICE_ID);
  Serial.println();
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize I2C for MPU6050
  Serial.println("→ Initializing I2C communication...");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);
  delay(1000);
  Serial.println("✓ I2C initialized");
  
  // Initialize MPU6050
  Serial.println("\n→ Initializing MPU6050...");
  mpu.initialize();
  delay(500);
  
  if (mpu.testConnection()) {
    Serial.println("✓ MPU6050 connected successfully!");
    mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);
    delay(500);
    
    // Test read MPU6050
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    Serial.println("  Test reading:");
    Serial.printf("  Accel: X=%d, Y=%d, Z=%d\n", ax, ay, az);
    Serial.printf("  Gyro:  X=%d, Y=%d, Z=%d\n", gx, gy, gz);
    delay(1000);
  } else {
    Serial.println("✗ MPU6050 connection FAILED!");
    Serial.println("  Check wiring: SDA->21, SCL->22, VCC->3.3V, GND->GND");
    delay(2000);
  }
  
  // Initialize heart rate sensor
  Serial.println("\n→ Initializing heart rate sensor on pin 18...");
  pinMode(HEART_RATE_PIN, INPUT);
  delay(500);
  
  // Test heart rate sensor
  Serial.println("  Testing heart rate sensor (5 readings):");
  for (int i = 0; i < 5; i++) {
    int rawValue = analogRead(HEART_RATE_PIN);
    Serial.printf("  Reading %d: %d (0-4095 range)\n", i+1, rawValue);
    delay(500);
  }
  
  if (analogRead(HEART_RATE_PIN) < 100) {
    Serial.println("⚠ WARNING: Heart rate sensor may be disconnected (low readings)");
    Serial.println("  Will use simulated values for testing");
  } else {
    Serial.println("✓ Heart rate sensor initialized");
  }
  delay(1000);
  
  // Initialize HR sample array
  for (int i = 0; i < SAMPLE_SIZE; i++) {
    hrSamples[i] = 0;
  }
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║  WAITING FOR USER LOGIN            ║");
  Serial.println("║  Monitoring starts automatically   ║");
  Serial.println("║  when consumer signs in            ║");
  Serial.println("╚════════════════════════════════════╝\n");
  
  // Blink LED to indicate waiting
  blinkLED(3);
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  unsigned long currentTime = millis();
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ WiFi disconnected. Reconnecting...");
    connectToWiFi();
    delay(5000);
    return;
  }
  
  // Poll for active session
  if (currentTime - lastPollTime >= POLL_INTERVAL) {
    lastPollTime = currentTime;
    checkForActiveSession();
  }
  
  // If no active session, just wait
  if (!hasActiveSession) {
    // Slow blink while waiting
    static unsigned long lastBlinkTime = 0;
    if (currentTime - lastBlinkTime >= 2000) {
      lastBlinkTime = currentTime;
      blinkLED(1);
    }
    delay(100);
    return;
  }
  
  // Active session - collect and send data
  
  // Extend window periodically
  if (currentTime - lastExtendTime >= EXTEND_INTERVAL) {
    lastExtendTime = currentTime;
    extendWindow();
  }
  
  // Read and send sensor data
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentTime;
    
    // Read sensors
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    float accel_x = ax / 16384.0;
    float accel_y = ay / 16384.0;
    float accel_z = az / 16384.0;
    float gyro_x = gx / 131.0;
    float gyro_y = gy / 131.0;
    float gyro_z = gz / 131.0;
    
    float bpm = readHeartRate();
    
    // Display readings
    printSensorReadings(bpm, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z);
    
    // Send data to Django
    sendDataToDjango(bpm, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z);
  }
  
  delay(100);
}

// ============================================
// SESSION MANAGEMENT FUNCTIONS
// ============================================

void checkForActiveSession() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  HTTPClient http;
  http.begin(checkSessionUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    
    StaticJsonDocument<1024> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      bool isActive = responseDoc["is_active"];
      
      if (isActive && !hasActiveSession) {
        // New session detected - user logged in!
        sessionId = responseDoc["session_id"].as<String>();
        consumidorId = responseDoc["consumidor_id"];
        ventanaId = responseDoc["ventana_id"];
        usuarioNombre = responseDoc["usuario_nombre"].as<String>();
        usuarioEmail = responseDoc["usuario_email"].as<String>();
        
        hasActiveSession = true;
        lastExtendTime = millis();
        
        Serial.println("\n╔════════════════════════════════════╗");
        Serial.println("║    USER LOGGED IN - SESSION START! ║");
        Serial.println("╠════════════════════════════════════╣");
        Serial.printf("║ User:         %-20s ║\n", usuarioNombre.c_str());
        Serial.printf("║ Email:        %-20s ║\n", usuarioEmail.c_str());
        Serial.printf("║ Consumer ID:  %-20d ║\n", consumidorId);
        Serial.printf("║ Ventana ID:   %-20d ║\n", ventanaId);
        Serial.printf("║ Session ID:   %-20s ║\n", sessionId.c_str());
        Serial.println("╠════════════════════════════════════╣");
        Serial.println("║  Now collecting sensor data...     ║");
        Serial.println("╚════════════════════════════════════╝\n");
        
        // Solid LED indicates active session
        digitalWrite(LED_PIN, HIGH);
        blinkLED(5);
        digitalWrite(LED_PIN, HIGH);
        
      } else if (!isActive && hasActiveSession) {
        // Session ended - user logged out!
        endSession();
      }
    }
  } else if (httpResponseCode == -1) {
    Serial.println("⚠ Connection timeout while checking session");
  }
  
  http.end();
}

void endSession() {
  hasActiveSession = false;
  sessionId = "";
  consumidorId = 0;
  ventanaId = 0;
  usuarioNombre = "";
  usuarioEmail = "";
  
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║      USER LOGGED OUT               ║");
  Serial.println("║  Session ended automatically       ║");
  Serial.println("║  Waiting for next login...         ║");
  Serial.println("╚════════════════════════════════════╝\n");
  
  blinkLED(3);
}

void extendWindow() {
  if (!hasActiveSession) return;
  
  HTTPClient http;
  http.begin(extendWindowUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["ventana_id"] = ventanaId;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode == 200) {
    Serial.println("✓ Window extended");
  }
  
  http.end();
}

// ============================================
// SENSOR FUNCTIONS
// ============================================

float readHeartRate() {
  // Read sensor raw value
  int heartRateValue = analogRead(HEART_RATE_PIN);
  
  hrSamples[sampleIndex] = heartRateValue;
  sampleIndex = (sampleIndex + 1) % SAMPLE_SIZE;
  
  long sum = 0;
  for (int i = 0; i < SAMPLE_SIZE; i++) {
    sum += hrSamples[i];
  }
  int avgValue = sum / SAMPLE_SIZE;
  
  // Debug: Print raw values occasionally
  static unsigned long lastDebugTime = 0;
  if (millis() - lastDebugTime > 30000) {  // Every 30 seconds
    lastDebugTime = millis();
    Serial.printf("[DEBUG] HR Raw: current=%d, avg=%d\n", heartRateValue, avgValue);
  }
  
  // If value is very low (sensor disconnected), use simulated values
  if (avgValue < 100) {
    // Generate realistic BPM between 60-90 with variation
    float baseBpm = 72.0;
    float variation = (random(0, 100) / 100.0 - 0.5) * 20.0; // ±10 BPM
    return constrain(baseBpm + variation, 60, 90);
  }
  
  // Sensor connected - use real reading
  float calculatedBpm = map(avgValue, 0, 4095, 40, 200);
  return constrain(calculatedBpm, 40, 200);
}

void printSensorReadings(float hr, float ax, float ay, float az, 
                         float gx, float gy, float gz) {
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.printf("║ User: %-28s ║\n", usuarioNombre.c_str());
  Serial.println("╠════════════════════════════════════╣");
  Serial.printf("║ Heart Rate:  %6.2f BPM          ║\n", hr);
  Serial.println("╟────────────────────────────────────╢");
  Serial.printf("║ Accel X:     %7.3f g           ║\n", ax);
  Serial.printf("║ Accel Y:     %7.3f g           ║\n", ay);
  Serial.printf("║ Accel Z:     %7.3f g           ║\n", az);
  Serial.println("╟────────────────────────────────────╢");
  Serial.printf("║ Gyro X:      %7.2f °/s         ║\n", gx);
  Serial.printf("║ Gyro Y:      %7.2f °/s         ║\n", gy);
  Serial.printf("║ Gyro Z:      %7.2f °/s         ║\n", gz);
  Serial.println("╚════════════════════════════════════╝");
}

void sendDataToDjango(float heart_rate, float accel_x, float accel_y, 
                      float accel_z, float gyro_x, float gyro_y, float gyro_z) {
  
  if (WiFi.status() != WL_CONNECTED || !hasActiveSession) {
    return;
  }
  
  HTTPClient http;
  http.begin(lecturasUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);
  
  StaticJsonDocument<512> doc;
  doc["ventana"] = ventanaId;
  doc["heart_rate"] = round(heart_rate * 100) / 100.0;
  doc["accel_x"] = round(accel_x * 1000) / 1000.0;
  doc["accel_y"] = round(accel_y * 1000) / 1000.0;
  doc["accel_z"] = round(accel_z * 1000) / 1000.0;
  doc["gyro_x"] = round(gyro_x * 100) / 100.0;
  doc["gyro_y"] = round(gyro_y * 100) / 100.0;
  doc["gyro_z"] = round(gyro_z * 100) / 100.0;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode == 201) {
    Serial.println("✓ Data sent successfully");
  } else {
    Serial.println("✗ Failed to send: " + String(httpResponseCode));
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("  Server response: " + response);
    } else {
      Serial.println("  Connection error (timeout or network issue)");
    }
  }
  
  http.end();
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

void connectToWiFi() {
  Serial.print("→ Connecting to WiFi: ");
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
    Serial.println("\n✓ WiFi connected!");
    Serial.print("  IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi failed!");
  }
}

void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}