# Arvis AI Assistant - Client

Desktop voice assistant with offline STT/TTS, LLM integration, and comprehensive security.

## Quick Start

1. Install Python 3.11 or 3.12
2. Run setup: ```INSTALL.bat```
3. Start Arvis: ```LAUNCH.bat```
4. Login: 
   - Username: ```admin```
   - Password: ```Admin123!@#```

## Documentation

- [Installation Guide](INSTALLATION_HELP.md)
- [User Management Guide](docs/USER_MANAGEMENT_GUIDE.md)
- [Security Guide](docs/RBAC_GUIDE.md)
- [2FA Setup](docs/USER_GUIDE_2FA.md)

## Repository Structure

- **Arvis-Client** (this repo) - Desktop client application
- **Arvis-Server** - Authentication and user management server

## Features

- 🎙️ Offline voice recognition (Vosk)
- 🔊 Natural TTS (Silero)
- 🤖 LLM integration (Ollama)
- 🔐 RBAC + 2FA security
- 🌐 Remote server authentication
- 📊 System monitoring

## Server Connection

To connect to remote authentication server:

1. Set in ```config/config.json```:{
   "security": {
     "auth": {
       "use_remote_server": true,
       "server_url": "http://your-server:8000"
     }
   }
}

2. Server repository: https://github.com/Fat1ms/Arvis-Server

## License

MIT
