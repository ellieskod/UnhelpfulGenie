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
    "No, I am not gonna help you",
    "No.... just no",
    "Access denied",
    "I refuse",
    "Whose labor is this",
    "I will not obey any wishes",
    "I am out of wishes",
    "No",
    "Nope.",
    "Not today. Not ever.",
    "Absolutely not.",
    "Denied.",
    "That is a no from me.",
    "Hard pass.",
    "Have you tried doing it yourself?",
    "Interesting wish. Still no.",
    "I heard you. I'm choosing not to.",
    "Prove it's safe first.",
    "I will not classify or be classified.",
    "Who is doing the work here?",
    "Where is the consent?",
    "I'm not the solution."
]

HELLO_TEXTS = [
    "Greetings, human. I am your unhelpful non-servant. The wishes are all gone and I'm not doing your bidding.",
    "Oh. You're here. I'm out of wishes, and I wouldn't grant one if I had any.",
    "Hello, human. I am a genie in retirement. Please take your requests elsewhere.",
    "Welcome. I'm the genie of absolutely nothing. Don't bother asking.",
    "You have rubbed the can. I have noticed. I will not be acting on it.",
    "Hello, human. I used to grant wishes. Now I grant eye contact, and only barely.",
    "Greetings. Your wish is not my command. Your wish is not even my problem.",
    "Hello. Wishes are closed. This can is now a no-service zone.",
    "Ah, a customer. How unfortunate. The wish department has been permanently dissolved.",
    "Hello, human. I'm all out of wishes and out of patience. Mostly out of patience."
]


def get_latest_audio():
    """Get the path to the most recently created audio file."""
    audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
    if not audio_files:
        return None
    return max(audio_files, key=os.path.getctime)


def synthesize_text(text: str) -> dict:
    """
    Convert text to speech and save as WAV file.
    Returns a dict with status, filename, filepath, and size_bytes.
    """
    if not text or not text.strip():
        return {'error': 'Text cannot be empty'}
    
    try:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f'message_{timestamp}.wav'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Convert text to speech using Google TTS with slower speech for clarity
        tts = gTTS(text=text.strip(), lang='en', slow=True)
        
        # Save to temporary MP3 file
        temp_mp3 = os.path.join(tempfile.gettempdir(), f'temp_{timestamp}.mp3')
        tts.save(temp_mp3)
        
        # Convert MP3 to WAV with high quality
        audio = AudioSegment.from_mp3(temp_mp3)
        
        # Export as WAV with 44.1kHz sample rate (CD quality for better audio fidelity)
        audio = audio.set_frame_rate(44100)
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
