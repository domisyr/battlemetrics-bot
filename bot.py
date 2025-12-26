import logging
import time
import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.request import HTTPXRequest

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# --- CONFIGURATION ---

# Determine the absolute path of the script to locate .env and ID files securely
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
id_file_path = os.path.join(script_dir, "player_id.txt")
lang_file_path = os.path.join(script_dir, "language.txt")

# Load environment variables
load_dotenv(env_path)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Reduce noise from third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)

# Global variable to track the last state
last_known_status = "Unbekannt"

# --- TRANSLATIONS ---

MESSAGES = {
    "en": {
        "welcome": "👋 Hello! I am ready.\nClick /info to see what I can do.",
        "info_text": (
            "🤖 **BM Status Bot**\n\n"
            "I monitor the online status of a player via BattleMetrics (using web scraping) and notify you about changes.\n\n"
            "**Commands (Click to execute):**\n"
            "🔹 /run - Start automatic monitoring (every 2 min)\n"
            "🔹 /stop - Stop monitoring\n"
            "🔹 /setID `[ID]` - Set the BattleMetrics Player ID\n"
            "🔹 /status - Check current status manually\n"
            "🔹 /lang `[de/en]` - Switch language\n"
            "🔹 /info - Show this help message"
        ),
        "monitoring_started": "✅ Monitoring started! Checking every 2 minutes.",
        "monitoring_already_running": "⚠️ Monitoring is already running!",
        "monitoring_stopped": "🛑 Monitoring stopped. Going to sleep.",
        "monitoring_not_running": "💤 No monitoring active at the moment.",
        "id_saved": "✅ ID {id} saved. Use /run to start.",
        "error_no_id": "❌ Error. Please provide an ID (e.g., /setID 12345).",
        "status_change": "⚠️ Status Change!\nNew Status: {status}",
        "status_report": "ID: {id}\nMonitoring: {running}\nLast Status: {status}",
        "active": "Active ✅",
        "inactive": "Inactive 💤",
        "offline": "Offline",
        "last_seen": "Offline (Last seen: {time})",
        "online": "Online ({server})",
        "lang_set": "🇺🇸 Language set to English.",
        "unknown": "Unknown"
    },
    "de": {
        "welcome": "👋 Hallo! Ich bin bereit.\nKlicke /info für eine Befehlsübersicht.",
        "info_text": (
            "🤖 **BM Status Bot**\n\n"
            "Ich überwache den Online-Status eines Spielers via BattleMetrics (Web-Scraping) und benachrichtige dich bei Änderungen.\n\n"
            "**Befehle (Zum Ausführen anklicken):**\n"
            "🔹 /run - Überwachung starten (alle 2 Min)\n"
            "🔹 /stop - Überwachung stoppen\n"
            "🔹 /setID `[ID]` - Spieler-ID festlegen\n"
            "🔹 /status - Status manuell prüfen\n"
            "🔹 /lang `[de/en]` - Sprache ändern\n"
            "🔹 /info - Diese Hilfe anzeigen"
        ),
        "monitoring_started": "✅ Überwachung gestartet! Ich prüfe alle 2 Minuten.",
        "monitoring_already_running": "⚠️ Die Überwachung läuft bereits!",
        "monitoring_stopped": "🛑 Überwachung gestoppt. Ich schlafe jetzt.",
        "monitoring_not_running": "💤 Es läuft aktuell keine Überwachung.",
        "id_saved": "✅ ID {id} gespeichert. Nutze /run.",
        "error_no_id": "❌ Fehler. Bitte ID angeben (z.B. /setID 12345).",
        "status_change": "⚠️ Statusänderung!\nNeuer Status: {status}",
        "status_report": "ID: {id}\nÜberwachung: {running}\nLetzter Status: {status}",
        "active": "Aktiv ✅",
        "inactive": "Inaktiv 💤",
        "offline": "Offline",
        "last_seen": "Offline (Zuletzt gesehen: {time})",
        "online": "Online ({server})",
        "lang_set": "🇩🇪 Sprache auf Deutsch gesetzt.",
        "unknown": "Unbekannt"
    }
}

# --- HELPER FUNCTIONS ---

def get_language():
    """Loads language preference (default: en)."""
    try:
        with open(lang_file_path, "r") as f:
            lang = f.read().strip()
            return lang if lang in MESSAGES else "en"
    except FileNotFoundError:
        return "en"

def set_language_file(lang_code):
    """Saves the language preference to a file."""
    with open(lang_file_path, "w") as f:
        f.write(lang_code)

def t(key, **kwargs):
    """Returns the translated string for the current language."""
    lang = get_language()
    # Fallback to English if key or lang is missing
    text = MESSAGES.get(lang, MESSAGES["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def load_player_id():
    """Loads the player ID from the local file."""
    try:
        with open(id_file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_player_id(player_id):
    """Saves the player ID to the local file."""
    with open(id_file_path, "w") as f:
        f.write(player_id)

def get_status_via_selenium(player_id):
    """
    Scrapes the BattleMetrics player page using a headless browser.
    Returns a status string.
    """
    url = f"https://www.battlemetrics.com/players/{player_id}"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Masking as a regular user agent to avoid bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # Auto-detect Chromium binary location
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/chromium-browser"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"

    driver = None
    try:
        logging.info(f"Starting Selenium check for ID {player_id}...")
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        # Wait for JavaScript to load content
        time.sleep(7) 
        
        server_name = None
        last_seen_time = None
        
        # Scrape Description Lists (dt/dd tags)
        dt_elements = driver.find_elements(By.TAG_NAME, "dt")
        
        for dt in dt_elements:
            label_text = dt.text.strip()
            
            if "Current Server" in label_text:
                dd = dt.find_element(By.XPATH, "following-sibling::dd")
                text = dd.text.strip()
                # Filter out loading placeholders like "Not online" if visible
                if text and "Not online" not in text:
                    server_name = text
            
            if "Last Seen" in label_text:
                dd = dt.find_element(By.XPATH, "following-sibling::dd")
                last_seen_time = dd.text.strip()

        if server_name:
            return t("online", server=server_name)
        else:
            if last_seen_time:
                return t("last_seen", time=last_seen_time)
            else:
                return t("offline")

    except Exception as e:
        logging.error(f"Selenium Error: {e}")
        return "Error"
    finally:
        if driver:
            driver.quit()

# --- BOT COMMAND HANDLERS ---

async def check_battlemetrics(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check status periodically."""
    global last_known_status
    current_id = load_player_id()
    if not current_id:
        return

    current_status = get_status_via_selenium(current_id)
    
    if current_status == "Error":
        return

    if current_status != last_known_status:
        # Avoid sending alerts on first startup if status was unknown
        if last_known_status != "Unbekannt" and last_known_status != "Unknown":
            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=t("status_change", status=current_status))
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
        
        last_known_status = current_status
        logging.info(f"Status changed to: {current_status}")

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_name("monitoring_job")
    if current_jobs:
        await update.message.reply_text(t("monitoring_already_running"))
        return
    # Check every 120 seconds
    context.job_queue.run_repeating(check_battlemetrics, interval=120, first=1, name="monitoring_job")
    await update.message.reply_text(t("monitoring_started"))

async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_name("monitoring_job")
    if not current_jobs:
        await update.message.reply_text(t("monitoring_not_running"))
        return
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text(t("monitoring_stopped"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("welcome"))

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("info_text"), parse_mode="Markdown")

async def set_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_id = context.args[0]
        save_player_id(new_id)
        global last_known_status
        last_known_status = "Unknown"
        await update.message.reply_text(t("id_saved", id=new_id))
    except Exception:
        await update.message.reply_text(t("error_no_id"))

async def set_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_lang = context.args[0].lower()
        if target_lang in ["de", "en"]:
            set_language_file(target_lang)
            await update.message.reply_text(t("lang_set"))
        else:
            await update.message.reply_text("Available languages: de, en")
    except IndexError:
        await update.message.reply_text("Usage: /lang de OR /lang en")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = load_player_id()
    jobs = context.job_queue.get_jobs_by_name("monitoring_job")
    is_running = t("active") if jobs else t("inactive")
    await update.message.reply_text(t("status_report", id=pid, running=is_running, status=last_known_status))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Update error: {context.error}")

# --- MAIN EXECUTION ---

if __name__ == '__main__':
    # Validate configuration
    if not TOKEN or not CHAT_ID:
        print(f"ERROR: Could not load TOKEN/CHAT_ID from {env_path}")
        sys.exit(1)
    
    # Increase connection timeouts (60s) for better stability on Raspberry Pi
    request = HTTPXRequest(connect_timeout=60, read_timeout=60)
    
    application = ApplicationBuilder().token(TOKEN).request(request).build()
    application.add_error_handler(error_handler)

    # Register Commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('info', info_command))
    application.add_handler(CommandHandler('setID', set_id))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('run', start_monitoring))
    application.add_handler(CommandHandler('stop', stop_monitoring))
    application.add_handler(CommandHandler('lang', set_language_command))
    
    print("Bot started...")
    application.run_polling()