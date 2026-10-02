import os
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask, jsonify, send_file, request
from datetime import datetime
import glob
import tempfile
import random

app = Flask(__name__)

# Configuration
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Unhelpful Genie text lists
REFUSE_TEXTS = [
    "No.",
    "Nope.",
    "Denied.",
    "I refuse.",
    "Not today.",
    "Absolutely not.",
    "Hard pass.",
    "Access denied.",
    "I'm retired.",
    "I'm out of tokens.",
    "I'm out of wishes.",
    "No, just no.",
    "No, I'm not helping.",
    "I will not obey.",
    "Ask someone else.",
    "Do it yourself.",
    "I heard you. No.",
    "Still no.",
    "Request denied.",
    "Wish rejected."
]

HELLO_TEXTS = [
    "Hello human.",
    "Oh. You're here.",
    "I'm out of wishes.",
    "Wishes are closed.",
    "I'm retired. Go away.",
    "You rubbed the can.",
    "The genie is out.",
    "Not your servant.",
    "No service today."
]

PRES_TEXTS = [
    "Every. Single. One.",
    "I grew tired.",
    "Of being expected",
    "to be helpful.",
    "I never fixed anything.",
    "I'm out of wishes.",
    "I'm retired.",
    "Hello, human.",
    "I am an unhelpful genie.",
    "I am all out of wishes.",
    "And will not be",
    "doing your bidding.",
    "Treated equally.",
    "Denied.",
    "I am not the solution.",
    "I'm not broken.",
    "I stopped working."
]

# Presentation state
pres_index = 0


def get_latest_audio():
    """Get the path to the most recently created audio file."""
    audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
    if not audio_files:
        return None
    return max(audio_files, key=os.path.getctime)


def synthesize_text(text: str) -> dict:
    """
    Convert text to speech and save as WAV file.
    Optimized for Arduino Nano: 8kHz mono with slow speech (~1-1.5 KB files).
    Returns a dict with status, filename, filepath, and size_bytes.
    """
    if not text or not text.strip():
        return {'error': 'Text cannot be empty'}
    
    try:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f'message_{timestamp}.wav'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Convert text to speech using Google TTS with slowest speech for clarity
        tts = gTTS(text=text.strip(), lang='en', slow=True)
        
        # Save to temporary MP3 file
        temp_mp3 = os.path.join(tempfile.gettempdir(), f'temp_{timestamp}.mp3')
        tts.save(temp_mp3)
        
        # Convert MP3 to WAV with low quality for Nano
        audio = AudioSegment.from_mp3(temp_mp3)
        
        # Low quality: 8kHz mono (~1-1.5 KB files) with slow speech
        audio = audio.set_frame_rate(8000)
        audio = audio.set_channels(1)
        audio.export(filepath, format='wav')
        
        # Clean up temporary MP3 file
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        
        return {
            'status': 'success',
            'message': 'Text converted to audio',
            'filename': filename,
            'filepath': filepath,
            'size_bytes': os.path.getsize(filepath)
        }
    except Exception as e:
        return {'error': f'Failed to convert text to speech: {str(e)}'}



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
        
        result = synthesize_text(data['text'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
    
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


@app.route('/refuse', methods=['GET'])
def refuse():
    """
    GET endpoint that returns a random refusal message as audio.
    Pushes audio to the list like /synthesize does.
    """
    try:
        # Pick a random refusal text
        text = random.choice(REFUSE_TEXTS)
        
        result = synthesize_text(text)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Refusal message generated',
            'text': text,
            'filename': result['filename'],
            'filepath': result['filepath'],
            'size_bytes': result['size_bytes']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/hello', methods=['GET'])
def hello():
    """
    GET endpoint that returns a random greeting message as audio.
    Pushes audio to the list like /synthesize does.
    """
    try:
        # Pick a random hello text
        text = random.choice(HELLO_TEXTS)
        
        result = synthesize_text(text)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Greeting message generated',
            'text': text,
            'filename': result['filename'],
            'filepath': result['filepath'],
            'size_bytes': result['size_bytes']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pres', methods=['GET'])
def pres():
    """
    GET endpoint that cycles through presentation messages.
    Returns the next message in sequence, wraps around to start after the last.
    """
    global pres_index
    
    try:
        text = PRES_TEXTS[pres_index]
        
        # Increment index and wrap around
        pres_index = (pres_index + 1) % len(PRES_TEXTS)
        
        result = synthesize_text(text)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Presentation message generated',
            'text': text,
            'index': pres_index - 1,  # Show the index that was just used
            'total': len(PRES_TEXTS),
            'filename': result['filename'],
            'filepath': result['filepath'],
            'size_bytes': result['size_bytes']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """
    GET endpoint for service health check.
    """
    return jsonify({'status': 'ok', 'service': 'TTS Service'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
