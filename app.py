import os
import pyttsx3
from flask import Flask, jsonify, send_file, request
from datetime import datetime
import glob

app = Flask(__name__)

# Configuration
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Initialize TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)  # Speed of speech


def get_latest_wav():
    """Get the path to the most recently created WAV file."""
    wav_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
    if not wav_files:
        return None
    return max(wav_files, key=os.path.getctime)


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
        
        # Save audio file
        tts_engine.save_to_file(text, filepath)
        tts_engine.runAndWait()
        
        return jsonify({
            'status': 'success',
            'message': 'Text converted to audio',
            'filename': filename,
            'filepath': filepath
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['GET'])
def download():
    """
    GET endpoint for Arduino to download the latest WAV file.
    """
    try:
        latest_file = get_latest_wav()
        
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
        wav_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
        wav_files.sort(key=os.path.getctime, reverse=True)
        
        files_info = []
        for filepath in wav_files:
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
