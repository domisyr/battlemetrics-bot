BM Status Bot - A Telegram Selenium Monitoring Bot

This bot uses Selenium to monitor a specific status on a website and notifies you via Telegram as soon as the status changes. It is designed to run reliably on servers or devices like a Raspberry Pi and can be fully controlled through Telegram commands.

The focus is on simplicity, reliability, and clear control via Telegram.

⸻

🚀 Features
	•	Telegram bot based on python-telegram-bot
	•	Website monitoring using Selenium (Chrome / Chromium)
	•	Automatic periodic checks
	•	Telegram notifications on status changes
	•	Multilingual support (English / German)
	•	Full control via Telegram commands
	•	Configuration via .env file
	•	Suitable for Raspberry Pi and server environments

⸻

📦 Requirements
	•	Python 3.9+
	•	Google Chrome or Chromium
	•	Matching ChromeDriver
	•	Telegram Bot Token

Python dependencies (see requirements.txt):

python-telegram-bot
selenium
python-dotenv


⸻

⚙️ Installation

1. Clone the repository

git clone <REPO-URL>
cd <REPO-FOLDER>

2. Create a virtual environment (recommended)

python3 -m venv venv
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt


⸻

🔐 Configuration

Create a .env file

Create a .env file in the project root directory:

TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

💡 The chat ID is required so the bot knows where it is allowed to send messages.

⸻

🧠 How it works
	•	The bot periodically opens a website using Selenium
	•	A specific element or status is extracted
	•	Changes are detected and compared with the last known state
	•	When a change occurs, you receive a Telegram notification

The last known status is stored internally to prevent notification spam.

⸻

🤖 Telegram Commands

Command	Description
/start	Starts the bot and shows a short introduction
/info	Displays bot information
/setID <ID>	Sets the player/object ID to monitor
/status	Shows current status and monitoring state
/run	Starts monitoring
/stop	Stops monitoring
/lang en	Switch language to English
/lang de	Switch language to German


⸻

🌍 Language Support

The bot supports English and German. The selected language is stored locally and persists across restarts.

⸻

🛠️ Running the Bot

python bot.py

If everything is configured correctly, you should see:

Bot started...


⸻

🧩 Common Issues
	•	❌ Missing or incompatible ChromeDriver
	•	❌ Telegram token or chat ID not set correctly
	•	❌ Chromium not installed (common on Raspberry Pi)
	•	❌ Website structure or element has changed

Logs are your best friend when troubleshooting.

⸻

📈 Possible Extensions
	•	Docker support
	•	Web UI for configuration
	•	Multiple monitored IDs
	•	Persistent database storage
	•	Health checks / watchdog

⸻

📝 License

Private or educational use. Feel free to modify and extend the project.

⸻

If this bot runs reliably, you set it up correctly. If it doesn’t, the issue is almost always Selenium or the runtime environment — not the bot itself. Stay patient, it’s worth it.