import os
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask, jsonify, send_file, request
from datetime import datetime
import glob
import tempfile

app = Flask(__name__)

# Configuration
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)


def get_latest_audio():
    """Get the path to the most recently created audio file."""
    audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
    if not audio_files:
        return None
    return max(audio_files, key=os.path.getctime)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'TTS Service'}), 200


@app.route('/synthesize', methods=['POST'])
def synthesize():
    """
    POST endpoint to convert text to speech and save as WAV.
    
    Expected JSON:
    {
        "text": "Your message here"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field in request body'}), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({'error': 'Text field cannot be empty'}), 400
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f'message_{timestamp}.wav'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        try:
            # Convert text to speech using Google TTS with slower speech for clarity
            # slow=True makes speech slower and clearer for Arduino playback
            tts = gTTS(text=text, lang='en', slow=True)
            
            # Save to temporary MP3 file
            temp_mp3 = os.path.join(tempfile.gettempdir(), f'temp_{timestamp}.mp3')
            tts.save(temp_mp3)
            
            # Convert MP3 to WAV with high quality
            audio = AudioSegment.from_mp3(temp_mp3)
            
            # Export as WAV with 16kHz sample rate (good for Arduino, reduces file size)
            # frame_rate=16000, channels=1 (mono) for embedded systems
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(filepath, format='wav', bitrate='192k', parameters=['-q:a', '9'])
            
            # Clean up temporary MP3 file
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
            
            return jsonify({
                'status': 'success',
                'message': 'Text converted to audio',
                'filename': filename,
                'filepath': filepath,
                'size_bytes': os.path.getsize(filepath)
            }), 201
        except Exception as e:
            return jsonify({'error': f'Failed to convert text to speech: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['GET'])
def download():
    """
    GET endpoint for Arduino to download the latest WAV file.
    """
    try:
        latest_file = get_latest_audio()
        
        if not latest_file:
            return jsonify({'error': 'No audio files available'}), 404
        
        return send_file(
            latest_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=os.path.basename(latest_file)
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list', methods=['GET'])
def list_files():
    """
    GET endpoint to list all available audio files.
    """
    try:
        audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
        audio_files.sort(key=os.path.getctime, reverse=True)
        
        files_info = []
        for filepath in audio_files:
            files_info.append({
                'filename': os.path.basename(filepath),
                'size_bytes': os.path.getsize(filepath),
                'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'count': len(files_info),
            'files': files_info
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
