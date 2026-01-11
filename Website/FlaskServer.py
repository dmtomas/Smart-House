#!/usr/bin/env python3
"""
Flask Server
Handles audio upload, processing, and response generation
Now with ESP32 light registration support
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from datetime import datetime
import tempfile
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create directories
UPLOAD_FOLDER = '/tmp/voice_assistant'
RESPONSE_FOLDER = '/tmp/voice_responses'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESPONSE_FOLDER, exist_ok=True)

# Spotify Configuration
SPOTIPY_CLIENT_ID = '75c4ed30249147ada9921b6fbf1aa7e7'
SPOTIPY_CLIENT_SECRET = 'e657ca2cbb42457a909f896c4356f16e'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'

# Initialize Spotify client
spotify_client = None

def get_spotify_client():
    """Get or create Spotify client with user authentication"""
    global spotify_client
    if spotify_client is None:
        try:
            sp_oauth = SpotifyOAuth(
                client_id=SPOTIPY_CLIENT_ID,
                client_secret=SPOTIPY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope='user-modify-playback-state user-read-playback-state',
                cache_path='/tmp/.spotify_cache',
                open_browser=False
            )
            spotify_client = spotipy.Spotify(auth_manager=sp_oauth)
            print("Spotify client initialized")
        except Exception as e:
            print(f"Error initializing Spotify: {e}")
            return None
    return spotify_client

# Voice processing endpoints (keeping your existing code)
@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Handle voice processing request"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_audio_path = os.path.join(UPLOAD_FOLDER, f'audio_{timestamp}_original.webm')
    wav_path = os.path.join(UPLOAD_FOLDER, f'audio_{timestamp}.wav')

    try:
        audio_file.save(temp_audio_path)
        print(f"Saved original audio to: {temp_audio_path}")

        print("Converting audio to WAV...")
        audio = AudioSegment.from_file(temp_audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format='wav')
        print(f"Converted audio saved to: {wav_path}")

        if not os.path.exists(wav_path):
            return jsonify({
                'success': False,
                'error': 'Audio conversion failed - WAV file not created'
            }), 500

        result = process_audio_file(wav_path)

        try:
            os.remove(temp_audio_path)
            os.remove(wav_path)
        except:
            pass

        return jsonify(result)

    except Exception as e:
        try:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except:
            pass

        return jsonify({
            'success': False,
            'error': f'Error processing audio: {str(e)}'
        }), 500

def process_audio_file(audio_file_path):
    """Process audio file and return transcript and response"""
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file_path) as source:
            print("Limpiando ruido de fondo...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Procesando audio...")
            audio_data = recognizer.record(source)

        print("Transcribiendo...")
        transcript = recognizer.recognize_google(audio_data, language="es-ES")
        print(f"Transcripción: {transcript}")

        response_text = process_command(transcript)
        audio_file = generate_audio_response(response_text)

        return {
            "success": True,
            "transcript": transcript,
            "response_text": response_text,
            "audio_file": audio_file
        }

    except sr.UnknownValueError:
        return {"success": False, "error": "No se pudo entender el audio"}
    except sr.RequestError as e:
        return {"success": False, "error": f"Error del servicio de reconocimiento: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Error procesando audio: {str(e)}"}

def process_command(text):
    """Process voice command and generate appropriate response"""
    text_lower = text.lower()

    if "canción" in text_lower or "música" in text_lower or "reproduce" in text_lower:
        song_query = ""
        if "canción" in text_lower:
            parts = text_lower.split("canción", 1)
            if len(parts) > 1:
                song_query = parts[1].strip()
        elif "música" in text_lower:
            parts = text_lower.split("música", 1)
            if len(parts) > 1:
                song_query = parts[1].strip()
        elif "reproduce" in text_lower:
            parts = text_lower.split("reproduce", 1)
            if len(parts) > 1:
                song_query = parts[1].strip()

        song_query = song_query.replace("de ", "").replace("la ", "").strip()

        if song_query:
            return play_spotify_song(song_query)
        else:
            return "¿Qué canción quieres escuchar?"

    elif "pausa" in text_lower or "detén" in text_lower or "para la música" in text_lower:
        return pause_spotify()
    elif "continúa" in text_lower or "reanuda" in text_lower:
        return resume_spotify()
    elif "hola" in text_lower or "buenos días" in text_lower or "buenas tardes" in text_lower:
        return "¡Hola! ¿En qué puedo ayudarte hoy?"
    elif "hora" in text_lower or "qué hora" in text_lower:
        current_time = datetime.now().strftime('%H:%M')
        return f"La hora actual es {current_time}"
    elif "fecha" in text_lower or "qué día" in text_lower or "día es" in text_lower:
        months = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        now = datetime.now()
        month_name = months[now.month]
        return f"Hoy es {now.day} de {month_name} de {now.year}"
    elif "clima" in text_lower or "tiempo" in text_lower:
        return "Lo siento, aún no tengo acceso a información meteorológica"
    elif "cámara" in text_lower or "movimiento" in text_lower:
        try:
            with open('/var/www/html/motion_alert.txt', 'r') as f:
                last_motion = float(f.read().strip())
                time_diff = datetime.now().timestamp() - last_motion
                if time_diff < 60:
                    return f"Se detectó movimiento hace {int(time_diff)} segundos"
                elif time_diff < 3600:
                    return f"El último movimiento fue hace {int(time_diff / 60)} minutos"
                else:
                    return "No se ha detectado movimiento reciente"
        except:
            return "No hay información de movimiento disponible"
    elif "cómo te llamas" in text_lower or "tu nombre" in text_lower:
        return "Soy tu asistente de voz de Casa. Puedes llamarme Asistente"
    elif "ayuda" in text_lower or "qué puedes hacer" in text_lower:
        return "Puedo decirte la hora, la fecha, consultar el estado de las cámaras, reproducir música en Spotify, y responder preguntas básicas"
    elif "gracias" in text_lower:
        return "¡De nada! Estoy aquí para ayudarte"
    elif "adiós" in text_lower or "hasta luego" in text_lower or "chau" in text_lower:
        return "¡Hasta luego! Que tengas un buen día"
    else:
        return f"Escuché: {text}. ¿Puedes reformular tu pregunta?"

def play_spotify_song(song_query):
    """Search and play a song on Spotify"""
    try:
        sp = get_spotify_client()
        if sp is None:
            return "No pude conectar con Spotify. Verifica la configuración"

        print(f"Searching Spotify for: {song_query}")
        results = sp.search(q=song_query, limit=1, type='track')

        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            track_uri = track['uri']

            devices = sp.devices()
            if not devices['devices']:
                return "No encontré ningún dispositivo de Spotify activo. Abre Spotify en tu teléfono o computadora"

            device_id = devices['devices'][0]['id']
            sp.start_playback(device_id=device_id, uris=[track_uri])

            return f"Reproduciendo {track_name} de {artist_name}"
        else:
            return f"No encontré ninguna canción llamada {song_query}"

    except Exception as e:
        print(f"Spotify error: {e}")
        return f"Error al reproducir música: {str(e)}"

def pause_spotify():
    """Pause Spotify playback"""
    try:
        sp = get_spotify_client()
        if sp is None:
            return "No pude conectar con Spotify"
        sp.pause_playback()
        return "Música pausada"
    except Exception as e:
        print(f"Spotify pause error: {e}")
        return "Error al pausar la música"

def resume_spotify():
    """Resume Spotify playback"""
    try:
        sp = get_spotify_client()
        if sp is None:
            return "No pude conectar con Spotify"
        sp.start_playback()
        return "Continuando la música"
    except Exception as e:
        print(f"Spotify resume error: {e}")
        return "Error al reanudar la música"

def generate_audio_response(text):
    """Generate audio file from text using Google TTS"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f"response_{timestamp}.mp3"
        audio_path = os.path.join(RESPONSE_FOLDER, audio_filename)

        tts = gTTS(text=text, lang='es')
        tts.save(audio_path)

        return f"/api/audio/{audio_filename}"

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    audio_path = os.path.join(RESPONSE_FOLDER, filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'voice_assistant'})

# ========== LIGHTS CONTROL API ==========

LIGHTS_FILE = '/home/tomas/lights_state.json'

def load_lights():
    """Load lights from JSON file"""
    try:
        with open(LIGHTS_FILE, 'r') as f:
            data = json.load(f)
            if data:
                return data
            return initialize_default_lights()
    except FileNotFoundError:
        return initialize_default_lights()
    except Exception as e:
        print(f"Error loading lights: {e}")
        return initialize_default_lights()

def initialize_default_lights():
    """Initialize with default lights"""
    default_lights = {
        'living': {
            'id': 'living',
            'name': 'Sala de Estar',
            'location': '📍 Planta Baja',
            'icon': '💡',
            'state': True
        },
        'kitchen': {
            'id': 'kitchen',
            'name': 'Cocina',
            'location': '📍 Planta Baja',
            'icon': '💡',
            'state': True
        },
        'bedroom': {
            'id': 'bedroom',
            'name': 'Habitación Principal',
            'location': '📍 Planta Alta',
            'icon': '💡',
            'state': False
        },
        'bathroom': {
            'id': 'bathroom',
            'name': 'Baño',
            'location': '📍 Planta Alta',
            'icon': '💡',
            'state': False
        },
        'garden': {
            'id': 'garden',
            'name': 'Jardín',
            'location': '📍 Exterior',
            'icon': '🌿',
            'state': False
        },
        'garage': {
            'id': 'garage',
            'name': 'Garaje',
            'location': '📍 Exterior',
            'icon': '🚗',
            'state': False
        }
    }
    save_lights_to_file(default_lights)
    return default_lights

def save_lights_to_file(lights_data):
    """Save lights to JSON file"""
    try:
        with open(LIGHTS_FILE, 'w') as f:
            json.dump(lights_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving lights: {e}")
        return False

# Initialize lights from file
lights_state = load_lights()

@app.route('/api/lights', methods=['GET'])
def get_lights():
    """Get all lights and their states"""
    return jsonify({
        'success': True,
        'lights': lights_state
    })

@app.route('/api/lights/<light_id>', methods=['GET'])
def get_light(light_id):
    """Get specific light state"""
    if light_id in lights_state:
        return jsonify({
            'success': True,
            'light': lights_state[light_id]
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Light not found'
        }), 404

@app.route('/api/lights/<light_id>/toggle', methods=['POST'])
def toggle_light_api(light_id):
    """Toggle a specific light"""
    data = request.get_json() or {}
    state = data.get('state')

    if light_id not in lights_state:
        lights_state[light_id] = {
            'id': light_id,
            'name': data.get('name', 'Unknown'),
            'location': data.get('location', 'Unknown'),
            'state': False
        }

    if state is not None:
        lights_state[light_id]['state'] = state
    else:
        lights_state[light_id]['state'] = not lights_state[light_id].get('state', False)

    save_lights_to_file(lights_state)

    return jsonify({
        'success': True,
        'light': lights_state[light_id]
    })

@app.route('/api/lights/sync', methods=['POST'])
def sync_lights():
    """Sync all lights state from frontend"""
    global lights_state
    data = request.get_json()

    if data and 'lights' in data:
        lights_state = data['lights']
        save_lights_to_file(lights_state)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Invalid data'}), 400

# ========== NEW: ESP32 REGISTRATION ENDPOINT ==========

@app.route('/api/lights/register', methods=['POST'])
def register_esp32_light():
    """
    Register a new light from ESP32
    Expected JSON format:
    {
        "id": "esp32_light_001",
        "name": "Luz del Comedor",
        "location": "Planta Baja",
        "icon": "💡",
        "state": false
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400

    # Validate required fields
    required_fields = ['id', 'name', 'location']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400

    light_id = data['id']

    # Check if light already exists
    if light_id in lights_state:
        # Update existing light (useful for reconnections)
        lights_state[light_id].update({
            'name': data['name'],
            'location': data['location'],
            'icon': data.get('icon', '💡')
            # Keep existing state
        })

        save_lights_to_file(lights_state)

        return jsonify({
            'success': True,
            'message': 'Light updated successfully',
            'light': lights_state[light_id],
            'action': 'updated'
        })

    # Create new light
    new_light = {
        'id': light_id,
        'name': data['name'],
        'location': data['location'],
        'icon': data.get('icon', '💡'),
        'state': data.get('state', False)
    }

    lights_state[light_id] = new_light
    save_lights_to_file(lights_state)

    print(f"New ESP32 light registered: {light_id} - {data['name']}")

    return jsonify({
        'success': True,
        'message': 'Light registered successfully',
        'light': new_light,
        'action': 'created'
    }), 201

@app.route('/api/lights/<light_id>/heartbeat', methods=['POST'])
def esp32_heartbeat(light_id):
    """
    Heartbeat endpoint for ESP32 to report status
    Expected JSON: { "state": true/false }
    """
    data = request.get_json() or {}

    if light_id not in lights_state:
        return jsonify({
            'success': False,
            'error': 'Light not registered. Please register first.'
        }), 404

    # Update state if provided
    if 'state' in data:
        lights_state[light_id]['state'] = data['state']
        save_lights_to_file(lights_state)

    return jsonify({
        'success': True,
        'light': lights_state[light_id]
    })

@app.route('/api/lights/<light_id>', methods=['DELETE'])
def delete_light(light_id):
    """Delete a light (for manual cleanup or ESP32 deregistration)"""
    if light_id in lights_state:
        del lights_state[light_id]
        save_lights_to_file(lights_state)

        return jsonify({
            'success': True,
            'message': 'Light deleted successfully'
        })

    return jsonify({
        'success': False,
        'error': 'Light not found'
    }), 404


if __name__ == '__main__':
    print("Starting Flask Voice Assistant Server...")
    print("Server will run on http://0.0.0.0:5000")
    print("ESP32 Registration endpoint: POST /api/lights/register")
    app.run(host='0.0.0.0', port=5000, debug=False)
