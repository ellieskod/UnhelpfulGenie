/*
  Arduino TTS Service Example
  
  This example demonstrates how to:
  1. Connect to WiFi
  2. Send text to the TTS service for conversion
  3. Download and play the latest WAV file
  
  Requirements:
  - Arduino with WiFi capability (Arduino MKR WiFi 1010, Arduino UNO R4 WiFi, etc.)
  - Libraries: WiFi, HTTPClient, ArduinoJson
  
  Install libraries via Arduino IDE:
  - Sketch → Include Library → Manage Libraries
  - Search for "ArduinoJson" and install by Benoit Blanchon
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// Service URL (from Railway deployment)
const char* serviceUrl = "https://your-railway-url.railway.app";

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  Serial.println("\n\nStarting Arduino TTS Client");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Example 1: Send text to be synthesized
  Serial.println("\n--- Sending text for synthesis ---");
  sendTextToSynthesize("Hello Arduino, this is your first message");
  
  delay(2000);
  
  // Example 2: Download the latest audio file
  Serial.println("\n--- Downloading latest audio ---");
  downloadLatestAudio();
  
  delay(2000);
  
  // Example 3: List available files
  Serial.println("\n--- Listing audio files ---");
  listAudioFiles();
}

void loop() {
  // Demonstrate health check every 30 seconds
  delay(30000);
  healthCheck();
}

/**
   Connect to WiFi network
*/
void connectToWiFi() {
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
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

/**
   Send text to the TTS service for synthesis
   @param text The text to convert to speech
*/
void sendTextToSynthesize(String text) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return;
  }
  
  HTTPClient http;
  String url = String(serviceUrl) + "/synthesize";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<256> doc;
  doc["text"] = text;
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.print("Sending: ");
  Serial.println(payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpCode);
    
    String response = http.getString();
    Serial.println("Response: " + response);
    
    // Parse response
    StaticJsonDocument<256> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      if (responseDoc["status"] == "success") {
        Serial.print("Filename: ");
        Serial.println(responseDoc["filename"].as<String>());
      }
    }
  } else {
    Serial.print("HTTP Request failed. Error: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

/**
   Download the latest WAV file from the service
   In a real application, you might save this to SPIFFS or SD card
   and play it through a speaker.
*/
void downloadLatestAudio() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return;
  }
  
  HTTPClient http;
  String url = String(serviceUrl) + "/download";
  
  http.begin(url);
  
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Download started...");
    
    int totalSize = http.getSize();
    Serial.print("File size: ");
    Serial.print(totalSize);
    Serial.println(" bytes");
    
    // In a real application, you would:
    // 1. Write the stream to SPIFFS or SD card
    // 2. Pass the file path to an audio library for playback
    
    // For now, just read and discard the data
    WiFiClient *stream = http.getStreamPtr();
    int bytesRead = 0;
    uint8_t buffer[256];
    
    while (http.connected() && (bytesRead < totalSize)) {
      size_t size = stream->available();
      if (size) {
        int c = stream->readBytes(buffer, ((size > sizeof(buffer)) ? sizeof(buffer) : size));
        bytesRead += c;
        
        if (bytesRead % 10240 == 0) {
          Serial.print(".");
        }
      }
      delay(1);
    }
    
    Serial.println("\nDownload complete!");
  } else {
    Serial.print("Download failed. HTTP code: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

/**
   List all available audio files on the service
*/
void listAudioFiles() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return;
  }
  
  HTTPClient http;
  String url = String(serviceUrl) + "/list";
  
  http.begin(url);
  
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    String response = http.getString();
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      if (doc["status"] == "success") {
        int count = doc["count"];
        Serial.print("Available files: ");
        Serial.println(count);
        
        JsonArray files = doc["files"];
        for (JsonObject file : files) {
          Serial.print("  - ");
          Serial.print(file["filename"].as<String>());
          Serial.print(" (");
          Serial.print(file["size_bytes"].as<int>());
          Serial.println(" bytes)");
        }
      }
    } else {
      Serial.println("Failed to parse JSON response");
    }
  } else {
    Serial.print("HTTP Request failed. Error: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }
  
  http.end();
}

/**
   Perform a health check on the service
*/
void healthCheck() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  HTTPClient http;
  String url = String(serviceUrl) + "/health";
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    Serial.println("✓ Service is healthy");
  } else {
    Serial.print("✗ Service health check failed: ");
    Serial.println(httpCode);
  }
  
  http.end();
}
