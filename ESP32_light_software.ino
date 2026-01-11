/*
 ESP32 WiFi Manager with Light Control
 
 On first boot, the ESP32 creates an access point called "ESP32-Setup"
 Connect to it and navigate to 192.168.4.1 to configure WiFi credentials
 After configuration, it will connect to your network and control the light
*/

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

// Configuration storage
Preferences preferences;

// Web server for configuration
WebServer server(80);

// Variables to store WiFi credentials
String stored_ssid = "";
String stored_password = "";

// Hardcoded server URL - change this to your API endpoint
const char* server_url = "http://192.168.1.143:5000/api/lights/light-1767668729823";  

const int LED_PIN = 2;
bool configMode = false;

// HTML page for WiFi configuration
const char* configPage = R"(
<!DOCTYPE html>
<html>
<head>
  <title>ESP32 WiFi Setup</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial; padding: 20px; background: #f0f0f0; }
    .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { color: #333; text-align: center; }
    input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
    button:hover { background: #45a049; }
    label { font-weight: bold; color: #555; }
  </style>
</head>
<body>
  <div class="container">
    <h1>WiFi Configuration</h1>
    <form action="/save" method="POST">
      <label>WiFi Network:</label>
      <input type="text" name="ssid" required placeholder="Enter WiFi SSID">
      
      <label>Password:</label>
      <input type="password" name="password" required placeholder="Enter WiFi Password">
      
      <button type="submit">Save & Connect</button>
    </form>
  </div>
</body>
</html>
)";

void handleRoot() {
  server.send(200, "text/html", configPage);
}

void handleSave() {
  if (server.hasArg("ssid") && server.hasArg("password")) {
    String ssid = server.arg("ssid");
    String password = server.arg("password");
    
    // Save to preferences
    preferences.begin("wifi-config", false);
    preferences.putString("ssid", ssid);
    preferences.putString("password", password);
    preferences.end();
    
    String response = R"(
      <!DOCTYPE html>
      <html>
      <head>
        <title>Saved</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { font-family: Arial; padding: 20px; background: #f0f0f0; text-align: center; }
          .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 10px; }
          h1 { color: #4CAF50; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Configuration Saved!</h1>
          <p>ESP32 will now restart and connect to your WiFi network.</p>
        </div>
      </body>
      </html>
    )";
    
    server.send(200, "text/html", response);
    delay(2000);
    ESP.restart();
  } else {
    server.send(400, "text/plain", "Missing parameters");
  }
}

void startConfigMode() {
  Serial.println("Starting Configuration Mode...");
  configMode = true;
  
  // Start Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP("ESP32-Setup", "12345678"); // AP name and password
  
  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);
  Serial.println("Connect to 'ESP32-Setup' (password: 12345678) and navigate to 192.168.4.1");
  
  // Setup web server
  server.on("/", handleRoot);
  server.on("/save", HTTP_POST, handleSave);
  server.begin();
}

bool connectToWiFi() {
  Serial.print("Connecting to ");
  Serial.println(stored_ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(stored_ssid.c_str(), stored_password.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println("\nFailed to connect to WiFi");
    return false;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  delay(1000);
  Serial.println("\n\nESP32 Light Controller Starting...");
  
  // Load saved credentials
  preferences.begin("wifi-config", true);
  stored_ssid = preferences.getString("ssid", "");
  stored_password = preferences.getString("password", "");
  preferences.end();
  
  // Check if credentials exist
  if (stored_ssid.length() > 0 && stored_password.length() > 0) {
    Serial.println("Found saved WiFi credentials");
    
    // Try to connect
    if (connectToWiFi()) {
      configMode = false;
      return; // Successfully connected, continue to loop
    } else {
      Serial.println("Stored credentials didn't work, entering config mode");
    }
  } else {
    Serial.println("No saved credentials found");
  }
  
  // Start configuration mode
  startConfigMode();
}

void loop() {
  if (configMode) {
    // Handle web server requests
    server.handleClient();
  } else {
    // Normal operation - check light status
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      
      http.begin(server_url);
      int httpResponseCode = http.GET();
      
      if (httpResponseCode > 0) {
        String payload = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, payload);
        
        if (!error) {
          bool isSuccessful = doc["success"];
          
          if (isSuccessful) {
            bool lightState = doc["light"]["state"];
            
            Serial.print("Light state: ");
            Serial.println(lightState ? "ON" : "OFF");
            
            digitalWrite(LED_PIN, lightState ? HIGH : LOW);
          } else {
            Serial.println("API returned success: false");
          }
        } else {
          Serial.print("JSON Parse failed: ");
          Serial.println(error.f_str());
        }
      } else {
        Serial.print("HTTP Error: ");
        Serial.println(httpResponseCode);
      }
      http.end();
    } else if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, attempting reconnect...");
      if (!connectToWiFi()) {
        Serial.println("Reconnect failed, entering config mode");
        startConfigMode();
      }
    }
    
    delay(500);
  }
}
