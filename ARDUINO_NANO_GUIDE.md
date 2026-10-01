# Arduino Nano Memory Optimization Guide

## The Problem

Arduino Nano has:
- **2 KB RAM** (extremely limited)
- 30 KB Flash storage

Standard Arduino WiFi sketches need:
- WiFi library (~1.2 KB)
- HTTPClient library (~0.5 KB)
- ArduinoJson library (~1 KB)
- Your code (~0.3 KB)

**Total: ~3 KB** = Out of memory crash! ❌

## The Solution

The `arduino_nano_minimal.ino` sketch is optimized for Nano's constraints:

### Memory Optimizations

1. **No JSON Parsing**
   - Removed ArduinoJson library entirely
   - Just download audio, don't parse responses
   - Saves ~1 KB

2. **PROGMEM Strings**
   ```cpp
   Serial.println(F("This string stays in Flash, not RAM"));
   ```
   - Uses `F()` macro to keep strings in program memory
   - Saves ~0.5 KB

3. **Minimal Buffering**
   ```cpp
   uint8_t buf[64]; // Small 64-byte buffer instead of large
   ```
   - Streams data in small chunks
   - Saves ~0.5 KB

4. **No Global String Objects**
   - Creates strings only when needed
   - Deletes immediately after use

### What It Does

✅ Connect to WiFi  
✅ Call `/refuse` endpoint  
✅ Call `/hello` endpoint  
✅ Download audio file from `/download`  

❌ Parse JSON responses  
❌ Store large buffers  
❌ Require external libraries  

## Upload Instructions

1. Download the sketch: `arduino_nano_minimal.ino`
2. Open Arduino IDE
3. Go to **Tools > Board > Arduino AVR Boards > Arduino Nano**
4. Go to **Tools > Processor > ATmega328P**
5. Set **Tools > Port** to your COM port
6. **Edit the WiFi credentials** at the top of the sketch:
   ```cpp
   const char* ssid = "YOUR_SSID";
   const char* password = "YOUR_PASSWORD";
   const char* serviceUrl = "https://your-railway-url.railway.app";
   ```
7. Click **Upload**

## Memory Usage Breakdown

| Component | Size |
|-----------|------|
| WiFi library | ~1.2 KB |
| HTTPClient | ~0.5 KB |
| Your code | ~0.2 KB |
| **Total** | **~1.9 KB** ✅ |

**Headroom: ~0.1 KB** for runtime variables

## Real-World Usage

### Option 1: Simple Loop
```cpp
void loop() {
  // Every 10 seconds, get a random message
  getRandomMessage(F("/refuse"));
  delay(10000);
}
```

### Option 2: Button Control
```cpp
void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    downloadAudio();
    delay(100); // Debounce
  }
}
```

### Option 3: SD Card Playback
```cpp
// Download audio to SD card
void downloadAudio() {
  HTTPClient http;
  http.begin(serviceUrl + F("/download"));
  int code = http.GET();
  
  if (code == 200) {
    File file = SD.open("audio.wav", FILE_WRITE);
    WiFiClient* stream = http.getStreamPtr();
    
    while (http.connected()) {
      if (stream->available()) {
        uint8_t byte = stream->read();
        file.write(byte);
      }
    }
    file.close();
  }
  http.end();
}
```

## Troubleshooting

### "Sketch too large" Error
- Remove Serial.println() debug statements
- Remove unused functions
- Check that you're using F() for all string literals

### "Out of memory" Error
- Your loop() is creating too many variables
- Move variable creation outside the loop
- Use static variables instead of local

### Won't Connect to WiFi
- Check WiFi credentials
- Nano might reset from power draw; add capacitor (470µF) across 5V/GND
- Use separate 5V power supply instead of USB

### Audio Won't Download
- Service URL must be accessible from your network
- Test with: `curl https://your-url/list`
- Add delay(5000) before first download to let system stabilize

## Tips for Success

1. **Power Supply Matters**
   - USB power is unstable for WiFi
   - Use regulated 5V supply with capacitors
   - Brown-outs cause random resets

2. **Keep Setup() Short**
   - Don't do heavy operations during setup
   - Move to loop() or use timer interrupts

3. **Wireless is Slow**
   - Add generous delays between requests
   - 3-5 seconds between calls minimum

4. **Monitor Memory**
   - Use Arduino IDE serial monitor
   - If crashes increase, you're running out of RAM

## If Still Having Issues

Consider upgrading to:
- **Arduino MKR WiFi 1010** (256 KB RAM)
- **Arduino UNO R4 WiFi** (262 KB RAM)
- **ESP32** (512 KB RAM, $8-15)

These make development much easier without the memory constraints!

## Success Indicators

✅ Serial monitor shows "IP: 192.168.x.x"  
✅ `/refuse` returns code 201  
✅ `/hello` returns code 201  
✅ `/download` returns code 200 with file size  
✅ No crashes during downloads  

Good luck! 🎉
