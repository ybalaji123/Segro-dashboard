/*
    Smart Segro — ESP32 Access Point (AP) Server
    ─────────────────────────────────────────────
    This code turns your ESP32 into a Wi-Fi Access Point and Web Server.
    The laptop connects to this network and fetches data via `GET /data`.
*/

#include <WiFi.h>
#include <WebServer.h>

// ── Configuration ────────────────────────────────────────────────────────
const char* AP_SSID     = "SmartSegro_WiFi";
const char* AP_PASSWORD = "smart_password";   // Must be at least 8 chars

// Port 80 for HTTP Server
WebServer server(80);

// ── Sensor Variables (Placeholder) ───────────────────────────────────────
// In your real implementation, read from these pins.
const int pinMetalSensor  = 4; // Inductive proximity
const int pinPlasticSensor = 5; // IR sensor

// State variables to hand off to the laptop
unsigned long currentId = 0;
String currentWasteType = "None";
String currentStatus    = "Idle";

bool newWasteDetected = false;

// ── HTTP Endpoints ───────────────────────────────────────────────────────

void handleGetSensorData() {
    // If no new dataset has been generated since boot, id = 0.
    // Construct JSON Response
    // Format: {"id": 1, "waste_type": "Metal", "status": "Collected"}
    String json = "{";
    json += "\"id\":" + String(currentId) + ",";
    json += "\"waste_type\":\"" + currentWasteType + "\",";
    json += "\"status\":\"" + currentStatus + "\"";
    json += "}";

    // Allow CORS so scripts can fetch easily
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", json);
}

// ── Setup & Loop ─────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    delay(1000);

    // Setup input pins
    pinMode(pinMetalSensor, INPUT);
    pinMode(pinPlasticSensor, INPUT);

    // 1. Start Access Point
    Serial.println("\n[!] Starting Access Point...");
    WiFi.softAP(AP_SSID, AP_PASSWORD);

    IPAddress IP = WiFi.softAPIP();
    Serial.print("[OK] AP IP address: ");
    Serial.println(IP); // Naturally this defaults to 192.168.4.1

    // 2. Configure HTTP Routes
    server.on("/data", HTTP_GET, handleGetSensorData);

    server.begin();
    Serial.println("[OK] HTTP server started");
}

void loop() {
    // Listen for incoming GET requests
    server.handleClient();

    // ── Placeholder Sensor Logic ──
    // Replace this section with your actual hardware interrupt/polling logic.
    // Example: If a metal object passes the sensor
    /*
    if (digitalRead(pinMetalSensor) == HIGH && !newWasteDetected) {
        currentId++;
        currentWasteType = "Metal";
        currentStatus = "Collected";
        newWasteDetected = true;
        Serial.println("Detected Metal!");
        delay(3000); // Debounce
        newWasteDetected = false;
    }
    */
}
