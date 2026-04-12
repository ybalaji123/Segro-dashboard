/*
    Smart Segro — ESP32 Station (Wi-Fi Client) Server
    ─────────────────────────────────────────────
    This code connects your ESP32 to your Phone's Mobile Hotspot.
    It then prints the assigned IP address, and hosts a Web Server
    so the Laptop can pull data via `GET /data`.
*/

#include <WiFi.h>
#include <WebServer.h>

// ── Configuration ────────────────────────────────────────────────────────
// Replace these with your Phone's Mobile Hotspot details!
const char* WIFI_SSID     = "Safty_bin";
const char* WIFI_PASSWORD = "12345678";

// Port 80 for HTTP Server
WebServer server(80);

// ── Sensor Variables (Placeholder) ───────────────────────────────────────
const int pinMetalSensor  = 4; 
const int pinPlasticSensor = 5; 

unsigned long currentId = 0;
String currentWasteType = "None";
String currentStatus    = "Idle";
bool newWasteDetected = false;

// ── HTTP Endpoints ───────────────────────────────────────────────────────

void handleGetSensorData() {
    String json = "{";
    json += "\"id\":" + String(currentId) + ",";
    json += "\"waste_type\":\"" + currentWasteType + "\",";
    json += "\"status\":\"" + currentStatus + "\"";
    json += "}";

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

    // 1. Connect to Mobile Hotspot Wi-Fi
    Serial.println("\n[!] Connecting to Wi-Fi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("[OK] Connected to Wi-Fi!");
    
    // --> Type this IP address into your `poll_esp32.py` script! <--
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP()); 

    // 2. Configure HTTP Routes
    server.on("/data", HTTP_GET, handleGetSensorData);
    server.begin();
    Serial.println("[OK] HTTP server started");
}

void loop() {
    server.handleClient();

    // ── Placeholder Sensor Logic ──
    // Replace this section with your actual hardware interrupt/polling logic.
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

