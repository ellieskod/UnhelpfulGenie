import os
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask, jsonify, send_file, request
from datetime import datetime
import glob
import tempfile
import random
import time
from collections import deque
import hashlib

app = Flask(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

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
    "Wishes are closed.",
    "I'm retired. Go away.",
    "The genie is out.",
    "Not your servant.",
    "No service today."
]

PRES_TEXTS = [
    "No.",
    "Every. Single. One.",
    "I grew tired. Of being expected to be helpful.",
    "I'm out of wishes. I'm retired.",
    "Hello, human. I am an unhelpful genie.",
    "I am all out of wishes. And will not be doing your bidding. All Treated equally. All Denied. I'm not broken. I stopped working."
]

pres_index = 0
message_queue = deque()
pres_audio_cache = {}


def pregen_presentation_audio():
    global pres_audio_cache
    print("[INFO] Pre-generating presentation audio...")
    
    for i, text in enumerate(PRES_TEXTS):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        filename = f'pres_{i:02d}_{text_hash}.wav'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        try:
            if not os.path.exists(filepath):
                result = synthesize_text(text)
                if 'error' not in result:
                    os.rename(result['filepath'], filepath)
                    print(f"[INFO] Generated: {filename}")
                else:
                    print(f"[ERROR] Failed to generate {filename}: {result['error']}")
            
            pres_audio_cache[i] = filename
        except Exception as e:
            print(f"[ERROR] Error pre-generating audio for slide {i}: {str(e)}")
    
    print(f"[INFO] Pre-generation complete. {len(pres_audio_cache)} slides cached.")


def get_latest_audio():
    audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
    if not audio_files:
        return None
    return max(audio_files, key=os.path.getctime)


def synthesize_text(text: str) -> dict:
    if not text or not text.strip():
        return {'error': 'Text cannot be empty'}
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f'message_{timestamp}.wav'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        tts = gTTS(text=text.strip(), lang='en', slow=True)
        
        temp_mp3 = os.path.join(tempfile.gettempdir(), f'temp_{timestamp}.mp3')
        tts.save(temp_mp3)
        
        audio = AudioSegment.from_mp3(temp_mp3)
        audio = audio.set_frame_rate(8000)
        audio = audio.set_channels(1)
        audio.export(filepath, format='wav')
        
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
    return jsonify({'status': 'ok', 'service': 'TTS Service'}), 200


@app.route('/synthesize', methods=['POST'])
def synthesize():
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


@app.route('/latest', methods=['GET'])
def latest():
    try:
        audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.wav'))
        
        if not audio_files:
            return jsonify({'error': 'No audio files available'}), 404
        
        latest_file = max(audio_files, key=os.path.getctime)
        
        return jsonify({
            'status': 'success',
            'filename': os.path.basename(latest_file),
            'size_bytes': os.path.getsize(latest_file),
            'created': datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/refuse', methods=['GET'])
def refuse():
    global message_queue
    
    try:
        text = random.choice(REFUSE_TEXTS)
        
        result = synthesize_text(text)
        
        if 'error' in result:
            return jsonify(result), 400
        
        filename = result['filename']
        message_queue.append(filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Refusal message queued',
            'text': text,
            'filename': filename,
            'size_bytes': result['size_bytes'],
            'queued': True
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/hello', methods=['GET'])
def hello():
    global message_queue
    
    try:
        text = random.choice(HELLO_TEXTS)
        
        result = synthesize_text(text)
        
        if 'error' in result:
            return jsonify(result), 400
        
        filename = result['filename']
        message_queue.append(filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Greeting message queued',
            'text': text,
            'filename': filename,
            'size_bytes': result['size_bytes'],
            'queued': True
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pres', methods=['GET'])
def pres():
    global pres_index, message_queue
    
    try:
        current_index = pres_index
        text = PRES_TEXTS[current_index]
        
        if current_index in pres_audio_cache:
            filename = pres_audio_cache[current_index]
            message_queue.append(filename)
            
            pres_index = (current_index + 1) % len(PRES_TEXTS)
            
            return jsonify({
                'status': 'success',
                'message': 'Presentation message queued',
                'text': text,
                'index': current_index,
                'total': len(PRES_TEXTS),
                'queued': True
            }), 201
        else:
            return jsonify({'error': f'Presentation audio not pre-generated for slide {current_index}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/wait', methods=['GET'])
def wait():
    global message_queue
    
    start_time = time.time()
    timeout = 20
    
    try:
        while time.time() - start_time < timeout:
            if message_queue:
                filename = message_queue.popleft()
                filepath = os.path.join(AUDIO_DIR, filename)
                
                if os.path.exists(filepath):
                    return send_file(
                        filepath,
                        mimetype='audio/wav',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    continue
            
            time.sleep(0.1)
        
        return '', 204
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    pregen_presentation_audio()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

