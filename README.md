# TTS Service for Arduino

A simple Flask-based Text-to-Speech (TTS) service that can be deployed directly to Railway. Provides endpoints for converting text to audio and downloading WAV files.

## Features

- ✅ Text-to-Speech conversion using gTTS (no system dependencies)
- ✅ High-quality WAV output optimized for embedded systems
- REST API endpoints for easy integration
- Arduino-friendly `/download` endpoint for fetching the latest audio
- Easy deployment to Railway from GitHub
- Persistent audio file storage

## API Endpoints

### POST `/synthesize`
Convert text to speech and save as WAV file.

**Request:**
```json
{
  "text": "Hello, this is a test message"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Text converted to audio",
  "filename": "message_20240101_120530_123.wav",
  "filepath": "/path/to/message_20240101_120530_123.wav",
  "size_bytes": 12345
}
```

**Audio Specs:**
- Format: WAV (PCM)
- Sample Rate: 44.1 kHz (CD quality for optimal clarity)
- Channels: Stereo
- Bitrate: Lossless
- Speech Speed: Slow (clear pronunciation)

### GET `/download`
Download the most recently created WAV file. Perfect for Arduino to fetch the latest message.

**Response:** Binary WAV file

### GET `/list`
List all available audio files.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "files": [
    {
      "filename": "message_20240101_120530_123.wav",
      "size_bytes": 45632,
      "created": "2024-01-01T12:05:30.123000"
    }
  ]
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "TTS Service"
}
```

## Local Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/UnhelpfulGenie.git
cd UnhelpfulGenie
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the service:
```bash
python app.py
```

The service will start on `http://localhost:5000`

### Test Endpoints

**Convert text to audio:**
```bash
curl -X POST http://localhost:5000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, Arduino!"}'
```

**Download latest WAV:**
```bash
curl -X GET http://localhost:5000/download -o latest.wav
```

**List all files:**
```bash
curl -X GET http://localhost:5000/list
```

## Deployment to Railway

### Steps

1. **Ensure your GitHub repository is public** and the code is pushed to GitHub.

2. **Go to [Railway.app](https://railway.app)**

3. **Sign in with GitHub** and authorize Railway to access your repositories.

4. **Create a new project:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select the `UnhelpfulGenie` repository
   - Railway will auto-detect the `Procfile` and deploy

5. **View your deployment:**
   - Once deployed, Railway will provide you with a public URL
   - Your service will be accessible at something like: `https://yourdomain-production.up.railway.app`

### Environment Variables (Optional)

If needed, set environment variables in Railway:
- `PORT`: Will be automatically set by Railway (default: 5000)

### Arduino Integration

Once deployed, your Arduino can:

**Fetch the latest audio:**
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void setup() {
  WiFi.begin("SSID", "PASSWORD");
  
  HTTPClient http;
  http.begin("https://your-railway-url.railway.app/download");
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    // Read WAV file and play it
    WiFiClient *stream = http.getStreamPtr();
    // ... handle audio stream
  }
}
```

**Send a message to be converted:**
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

void sendMessage(String text) {
  HTTPClient http;
  http.begin("https://your-railway-url.railway.app/synthesize");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["text"] = text;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  http.end();
}
```

## File Structure

```
UnhelpfulGenie/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version specification
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── audio_files/          # Directory for storing WAV files (auto-created)
```

## Troubleshooting

### No audio device available (Linux/Docker)
pyttsx3 may need additional dependencies. In Docker, add to your build:
```bash
apt-get install -y espeak ffmpeg
```

### Audio files not persisting
Railway uses ephemeral storage by default. Consider adding a volume or external storage if you need persistent audio files across deployments.

### Large audio files
WAV files can be large. Monitor your storage and consider cleaning up old files or using a different audio format.

## Customization

### Change speech speed
Edit `app.py` line with `slow=True` parameter in gTTS initialization:
- `slow=True` - Slower, clearer speech (default, better for Arduino)
- `slow=False` - Normal speed (faster)

### Adjust audio sample rate
Edit the `set_frame_rate()` call in `app.py`:
- `44100` - 44.1 kHz (current, CD quality, better for high-fidelity audio)
- `16000` - 16 kHz (lower quality but smaller files, optimized for embedded systems)
- `22050` - 22.05 kHz (middle ground)

### Change audio channels
To modify audio channels, add this line after `audio = AudioSegment.from_mp3(temp_mp3)`:
- `audio = audio.set_channels(1)` - Mono (smaller files)
- `audio = audio.set_channels(2)` - Stereo (current, better quality)

### Add authentication
Wrap endpoints with authentication (e.g., using Flask-HTTPAuth):
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@app.route('/synthesize', methods=['POST'])
@auth.login_required
def synthesize():
    ...
```

## License

MIT

## Support

For issues or questions, open an issue on GitHub.
