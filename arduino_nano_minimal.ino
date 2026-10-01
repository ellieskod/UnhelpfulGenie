/*
  Unhelpful Genie TTS - Arduino Nano Minimal Edition
  
  This is heavily optimized for the Nano's 2KB RAM limit:
  - NO ArduinoJson (too heavy!)
  - NO JSON parsing
  - Simple HTTP GET only
  - Direct audio streaming
  - All strings in PROGMEM using F() macro
  
  Upload with: Tools > Board > Arduino AVR Boards > Arduino Nano
               Tools > Processor > ATmega328P
*/

#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials (EDIT THESE)
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* serviceUrl = "https://your-railway-url.railway.app";

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  Serial.println(F("\n=== Unhelpful Genie TTS ==="));
  connectToWiFi();
  
  // Option 1: Get refusal
  Serial.println(F("\n[1] Getting refusal..."));
  getRandomMessage(F("/refuse"));
  
  delay(3000);
  
  // Option 2: Get greeting  
  Serial.println(F("\n[2] Getting greeting..."));
  getRandomMessage(F("/hello"));
  
  delay(3000);
  
  // Option 3: Download latest audio
  Serial.println(F("\n[3] Downloading audio..."));
  downloadAudio();
}

void loop() {
  // Do nothing after setup
  delay(1000);
}

/**
   Connect to WiFi with minimal memory usage
*/
void connectToWiFi() {
  Serial.print(F("WiFi: "));
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(F("."));
    attempts++;
  }
  
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("IP: "));
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(F("WiFi FAILED"));
  }
}

/**
   Get a random message (/refuse or /hello)
   Just download, don't parse
*/
void getRandomMessage(const char* endpoint) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("Not connected"));
    return;
  }
  
  HTTPClient http;
  
  // Build URL in SRAM minimal way
  String url = String(serviceUrl) + endpoint;
  
  http.begin(url);
  int code = http.GET();
  
  if (code == 201) {
    Serial.print(F("OK ("));
    Serial.print(code);
    Serial.println(F(")"));
    
    // Get size to know we got something
    int len = http.getSize();
    Serial.print(F("Size: "));
    Serial.print(len);
    Serial.println(F(" bytes"));
  } else {
    Serial.print(F("Error: "));
    Serial.println(code);
  }
  
  http.end();
}

/**
   Download latest audio file directly
   Streams to Serial for monitoring (or SD card in real implementation)
*/
void downloadAudio() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("Not connected"));
    return;
  }
  
  HTTPClient http;
  String url = String(serviceUrl) + F("/download");
  
  http.begin(url);
  int code = http.GET();
  
  if (code == 200) {
    int totalSize = http.getSize();
    Serial.print(F("Downloading: "));
    Serial.print(totalSize);
    Serial.println(F(" bytes"));
    
    // Stream audio directly without buffering
    // In real project, write to SD card or audio codec here
    WiFiClient* stream = http.getStreamPtr();
    int bytesRead = 0;
    uint8_t buf[64]; // Small buffer for embedded systems
    
    while (http.connected() && bytesRead < totalSize) {
      size_t available = stream->available();
      if (available) {
        int len = stream->readBytes(buf, min((size_t)64, available));
        bytesRead += len;
        
        // Show progress every 10KB
        if (bytesRead % 10240 == 0) {
          Serial.print(F("."));
        }
      }
      delay(1); // Prevent watchdog timeout
    }
    
    Serial.println();
    Serial.println(F("Download complete!"));
  } else {
    Serial.print(F("Download failed: "));
    Serial.println(code);
  }
  
  http.end();
}

// Helper for min()
int min(int a, int b) {
  return a < b ? a : b;
}
