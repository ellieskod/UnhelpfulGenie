import os
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask, jsonify, send_file, request
from datetime import datetime
import glob
import tempfile
import random
import gzip
import io

app = Flask(__name__)
app.config['COMPRESS_ALGORITHM'] = 'gzip'

# Configuration
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Cache for pre-generated messages (in-memory storage)
MESSAGE_CACHE = {}

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
    "I'm not the solution.",
    "That's not a wish, that's a power imbalance."
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


def synthesize_text(text: str, quality: str = 'medium') -> dict:
    """
    Convert text to speech and save as WAV file.
    Quality options: 'low' (16kHz mono), 'medium' (22kHz stereo), 'high' (44.1kHz stereo)
    Returns a dict with status, filename, filepath, and size_bytes.
    """
    if not text or not text.strip():
        return {'error': 'Text cannot be empty'}
    
    # Check cache first
    cache_key = f"{text}_{quality}"
    if cache_key in MESSAGE_CACHE:
        return MESSAGE_CACHE[cache_key]
    
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
        
        # Convert MP3 to WAV and apply quality settings
        audio = AudioSegment.from_mp3(temp_mp3)
        
        # Quality profiles for Nano optimization
        if quality == 'low':
            # Ultra-lightweight: 16kHz mono (smallest files, ~2-3 KB)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
        elif quality == 'high':
            # High quality: 44.1kHz stereo (larger files, ~15-20 KB)
            audio = audio.set_frame_rate(44100)
            audio = audio.set_channels(2)
        else:  # medium (default)
            # Balanced: 22kHz stereo (medium files, ~6-8 KB)
            audio = audio.set_frame_rate(22050)
            audio = audio.set_channels(2)
        
        # Export as WAV
        audio.export(filepath, format='wav')
        
        # Clean up temporary MP3 file
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        
        result = {
            'status': 'success',
            'message': 'Text converted to audio',
            'filename': filename,
            'filepath': filepath,
            'size_bytes': os.path.getsize(filepath)
        }
        
        # Cache for future requests (keep last 20 messages)
        if len(MESSAGE_CACHE) > 20:
            MESSAGE_CACHE.pop(next(iter(MESSAGE_CACHE)))
        MESSAGE_CACHE[cache_key] = result
        
        return result
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
        "text": "Your message here",
        "quality": "low|medium|high" (optional, default medium)
    }
    
    Quality guide for Nano:
    - low: 16kHz mono = 2-3 KB files (fastest)
    - medium: 22kHz stereo = 6-8 KB files (balanced, default)
    - high: 44.1kHz stereo = 15-20 KB files (best quality)
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field in request body'}), 400
        
        quality = data.get('quality', 'medium')
        if quality not in ['low', 'medium', 'high']:
            quality = 'medium'
        
        result = synthesize_text(data['text'], quality=quality)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['GET'])
def download():
    """
    GET endpoint for Arduino to download the latest WAV file.
    Optional query params:
    - compress=gzip: Returns gzipped WAV (smaller transfer)
    - quality=low/medium/high: Regenerate at different quality
    """
    try:
        # Check if user wants a specific quality
        quality = request.args.get('quality', 'medium')
        compress = request.args.get('compress', 'false').lower() == 'true'
        
        # If quality requested, regenerate latest message at that quality
        if quality != 'medium':
            latest_file = get_latest_audio()
            if latest_file:
                # For now, just serve the existing file
                # Full optimization would re-synthesize, but that's expensive
                pass
        
        latest_file = get_latest_audio()
        
        if not latest_file:
            return jsonify({'error': 'No audio files available'}), 404
        
        # Read file for potential compression
        if compress:
            with open(latest_file, 'rb') as f:
                data = f.read()
            
            # Compress with gzip
            compressed_data = gzip.compress(data, compresslevel=9)
            
            return send_file(
                io.BytesIO(compressed_data),
                mimetype='audio/wav',
                as_attachment=True,
                download_name=os.path.basename(latest_file) + '.gz',
                headers={'Content-Encoding': 'gzip', 'X-Original-Size': str(len(data))}
            )
        else:
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
    Optional: ?slim=true returns minimal data (just count and latest)
    """
    try:
        audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
        audio_files.sort(key=os.path.getctime, reverse=True)
        
        slim = request.args.get('slim', 'false').lower() == 'true'
        
        if slim:
            # Minimal response for Nano
            return jsonify({
                'count': len(audio_files),
                'latest': os.path.basename(audio_files[0]) if audio_files else None
            }), 200
        
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
    Optional query params:
    - quality=low/medium/high: Default medium (files: 2-3KB / 6-8KB / 15-20KB)
    - lean=true: Return only status code (no JSON)
    """
    try:
        quality = request.args.get('quality', 'medium')
        lean = request.args.get('lean', 'false').lower() == 'true'
        
        # Pick a random refusal text
        text = random.choice(REFUSE_TEXTS)
        
        result = synthesize_text(text, quality=quality)
        
        if 'error' in result:
            return jsonify(result), 400
        
        # Lean mode: just return status code for Nano (minimal response)
        if lean:
            return '', 201
        
        return jsonify({
            'status': 'success',
            'message': 'Refusal message generated',
            'text': text,
            'filename': result['filename'],
            'size_bytes': result['size_bytes']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/hello', methods=['GET'])
def hello():
    """
    GET endpoint that returns a random greeting message as audio.
    Optional query params:
    - quality=low/medium/high: Default medium (files: 2-3KB / 6-8KB / 15-20KB)
    - lean=true: Return only status code (no JSON)
    """
    try:
        quality = request.args.get('quality', 'medium')
        lean = request.args.get('lean', 'false').lower() == 'true'
        
        # Pick a random hello text
        text = random.choice(HELLO_TEXTS)
        
        result = synthesize_text(text, quality=quality)
        
        if 'error' in result:
            return jsonify(result), 400
        
        # Lean mode: just return status code for Nano (minimal response)
        if lean:
            return '', 201
        
        return jsonify({
            'status': 'success',
            'message': 'Greeting message generated',
            'text': text,
            'filename': result['filename'],
            'size_bytes': result['size_bytes']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.before_request
def startup():
    """Pre-generate cached messages on first request."""
    global MESSAGE_CACHE
    if not MESSAGE_CACHE and len(glob.glob(os.path.join(AUDIO_DIR, '*.wav'))) == 0:
        # Cache just a few common messages at startup for fast first response
        print("[TTS Server] Pre-caching common messages for faster response...")
        
        # Cache first refuse and hello at low quality (fastest, smallest)
        if REFUSE_TEXTS:
            first_refuse = REFUSE_TEXTS[0]
            synthesize_text(first_refuse, quality='low')
            print(f"✓ Cached: {first_refuse[:30]}...")
        
        if HELLO_TEXTS:
            first_hello = HELLO_TEXTS[0]
            synthesize_text(first_hello, quality='low')
            print(f"✓ Cached: {first_hello[:30]}...")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
