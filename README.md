# 🏠 Smart Home System

A complete smart home automation system built with Flask, ESP32, and modern web technologies. Control lights, monitor cameras, interact with voice commands, and integrate with Spotify - this is controlled by web interface. The final objective of this project is to control most devices in the house using either voice commands or the phone while minimizing the amount of data sent to companies.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![ESP32](https://img.shields.io/badge/ESP32-Compatible-red.svg)
![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)

---

> **⚠️ Development Notice**
> 
> This project is currently under active development as a **learning platform** for:
> - Server management and web service deployment
> - Hardware-software integration with IoT devices
> - Real-time communication between web interfaces and microcontrollers
> - RESTful API design and implementation
> - Network protocols and client-server architecture
> 
> Features may change, and bugs are expected. Contributions, suggestions, and feedback are highly appreciated as part of the learning process!

---

## ✨ Features

### 🎛️ Smart Light Control
- **Web-based control panel** for all connected lights
- **ESP32 auto-registration** - lights appear automatically when configured
- **Real-time state synchronization** between web and hardware
- **Master controls** - turn any light on/off from website.

### 📹 Camera & Motion Detection
- **Live camera feeds** via MJPEG streams
- **Motion detection alerts** with timestamp tracking
- **Multi-camera support** with easy configuration
- **Responsive grid layout** for viewing multiple cameras

### 🎤 Voice Assistant (Spanish)
- **Voice command processing** using Google Speech Recognition. (temporary)
- **Text-to-Speech responses** via Google TTS. (temporary)
- **Spotify integration** - play, pause, resume music by voice
- **Smart home queries** - time, date, camera status
- **Extensible command system**

### 🎵 Spotify Integration
- **Voice-controlled playback** - search and play songs (Bugg refering to HTTP not having automatic permision to open microphone)
- **Multi-device support** - works with any Spotify Connect device (Curretly buggs with required cookies)
- **Playback control** - play, pause, resume

### 🤖 AI Assistant Interface
- Clean, modern chat interface
- Integration ready for AI services.

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **Flask-CORS** - Cross-origin resource sharing
- **SpeechRecognition** - Voice input processing
- **gTTS** - Google Text-to-Speech (temporary)
- **Spotipy** - Spotify Web API integration
- **PyDub** - Audio file processing

### Frontend
- **Pure HTML/CSS/JavaScript** - No framework dependencies
- **Responsive design** - Works on mobile and desktop
- **Modern UI** - Gradient backgrounds, smooth animations
- **Real-time updates** - Automatic state synchronization

### Hardware
- **ESP32** microcontrollers
- **WiFi connectivity** with auto-configuration
- **Relay modules** for light control
- **Reset functionality** - 5-second hold to factory reset

## 📋 Prerequisites

### Server Requirements
- Python 3.8 or higher
- Flask and dependencies
- LAN connectivity
- Microphone (for voice features)

### ESP32 Requirements
- ESP32 development board
- Arduino IDE with ESP32 support
- Required libraries:
  - WiFi
  - WebServer
  - HTTPClient
  - ArduinoJson
  - Preferences
  - nvs_flash

### Spotify (Optional)
- Spotify Premium account
- Spotify Developer App credentials


## 📱 Usage

### Web Interface
Access the web interface at `http://YOUR_SERVER_IP:5000` or by opening the HTML files directly.

**Navigation:**
- **/** - Home dashboard
- **/camaras** - Camera feeds and motion detection
- **/luces** - Light control panel
- **/IA** - AI assistant chat interface

### Adding a New Light

#### Method: Auto-Registration (ESP32)
1. Flash the ESP32 code to your device
2. Power on the ESP32
3. Connect to "ESP32-Setup" WiFi network
4. Open http://192.168.4.1 in your browser
5. Enter WiFi credentials, light name, and location
6. Save - the light will appear automatically in the web interface

### Factory Reset ESP32
Hold the boot button (GPIO 0) for 5 seconds to completely erase all configuration and return to setup mode.

### Voice Commands (Spanish)

| Command | Action |
|---------|--------|
| "Reproduce [canción]" | Play a song on Spotify |
| "Pausa la música" | Pause playback |
| "Continúa la música" | Resume playback |
| "¿Qué hora es?" | Get current time |
| "¿Qué día es hoy?" | Get current date |
| "Estado de las cámaras" | Get motion detection status |
| "Hola" | Greeting |
| "Gracias" | Thank you |



## 🔧 API Endpoints

### Lights API
```
GET    /api/lights              - Get all lights
GET    /api/lights/<id>         - Get specific light
POST   /api/lights/register     - Register new ESP32 light
POST   /api/lights/<id>/toggle  - Toggle light state
POST   /api/lights/<id>/heartbeat - ESP32 status update
POST   /api/lights/sync         - Sync all lights state
DELETE /api/lights/<id>         - Delete a light
```

### Voice API
```
POST   /api/process_voice       - Process audio and return response
GET    /api/audio/<filename>    - Serve generated audio files
```

### Health Check
```
GET    /health                  - Server status
```

## 📁 Project Structure

```
casa-smart-home/
├── server.py                    # Main Flask server
├── esp32_light_controller.ino   # ESP32 firmware
├── index.html                   # Home page
├── camaras.html                 # Camera monitoring page
├── luces.html                   # Light control page
├── IA.html                      # AI assistant page
├── lights_state.json            # Persistent light state storage
└── README.md                    # This file
```

## 🔐 Security Notes

- Change default ESP32 AP password ("12345678")
- Use HTTPS in production
- Implement authentication for web interface
- Secure Spotify credentials
- Use environment variables for sensitive data
- Keep firmware updated

## 🐛 Troubleshooting

### ESP32 Won't Connect to WiFi
- Verify WiFi credentials are correct
- Check signal strength
- Hold boot button for 5 seconds to reset
- Check serial monitor for error messages

### Lights Not Responding
- Verify server is running
- Check ESP32 serial monitor for connection status
- Ensure ESP32 and server are on same network
- Try reloading the lights page (🔄 Actualizar button)

### Voice Commands Not Working
- Check microphone permissions
- Verify internet connection (Google API required) (temporary)
- Check browser console for errors
- Ensure audio format is supported

### Spotify Integration Issues
- Verify Spotify Premium account
- Check API credentials
- Ensure redirect URI matches exactly
- Open Spotify app on a device for playback

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
