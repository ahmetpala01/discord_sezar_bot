# Sezar Bot

A multipurpose Discord bot offering Music, Chat, and Utility features.

<div align="center">

![Discord Bot Status](https://img.shields.io/badge/status-online-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)  
![Docker](https://img.shields.io/badge/docker-supported-blue)

</div>

## 🌟 Features

- 🎵 **Music Player**: Play, pause, and manage music from YouTube
- 💬 **Chat AI**: Answer questions and engage in conversations
- 🎮 **Steam Profile**: View Steam user information
- 📊 **Speed Test**: Test the server's internet speed
- 🎲 **Word Game**: Play Turkish word game with special linguistic rules
- 🔧 **Moderation**: Basic moderation tools for server management
- 📈 **Statistics**: Track message statistics and user activity

## 📋 Commands

### 🎵 Music Commands
| Command | Description |
|---------|-------------|
| `/play <song name or URL>` | Play music from YouTube |
| `/pause` | Pause the current song |
| `/resume` | Resume paused music |
| `/stop` | Stop the music playback |
| `/join` | Join your voice channel |
| `/leave` | Leave the voice channel |

### 💬 Chat Commands
| Command | Description |
|---------|-------------|
| `/sorusor <question>` | Ask a question to the bot |
| `/sohbet <message>` | Chat with the bot |
| `@Sezar Bot <message>` | Mention the bot to start a conversation |

### 🛠️ Utility Commands
| Command | Description |
|---------|-------------|
| `/steamprofil <username>` | Show Steam profile information |
| `/speedtest` | Run an internet speed test |
| `/sunucubilgi` | Display server information |
| `/botbilgi` | Display technical information about the bot |
| `/help [command]` | Show help information for all commands or a specific one |

### 🎲 Word Game Commands
| Command | Description |
|---------|-------------|
| `/kelimeoyunu` | Start the Turkish word game |
| `/bitir` | End the active word game |

### 🔒 Moderation Commands
| Command | Description |
|---------|-------------|
| `/warn <member> <reason>` | Warn a server member |
| `/warnings <member>` | Show warnings for a server member |

## 💻 Self-Hosting

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token
- Steam API Key (for Steam features)
- FFmpeg (for voice support)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discord_sezar_bot.git
   cd discord_sezar_bot
   ```

2. Create an environment file:
   ```bash
   echo "DISCORD_BOT_TOKEN=your_token_here" > .env
   echo "STEAM_API_KEY=your_api_key_here" >> .env
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

### Docker Support

You can also run the bot using Docker:

```bash
docker-compose up -d
```

To free up disk space when needed:
```bash
bash docker-cleanup.sh
```

## 🎮 Status Messages

Sezar Bot regularly changes its status to highlight different features:
- 🎵 Listening to "Music | /play"
- 🎮 Playing "Steam info | /steamprofil"
- 👀 Watching "Your questions | /sorusor"
- 🏆 Competing in "Fastest bot | /speedtest"

## 🔗 Invite

[Click here](https://discord.com/oauth2/authorize?client_id=1372553389539328151) to add Sezar Bot to your server!

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests if you have suggestions for improvements or new features.

## 📜 License

This project is open-source. Please include appropriate credits if you fork or modify it.