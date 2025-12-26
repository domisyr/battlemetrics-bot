#!/bin/bash

# Farben für schöne Ausgaben
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starte Installation des BM Status Bots...${NC}"

# 1. System-Updates und Chromium installieren
echo -e "${GREEN}📦 Installiere Chromium und Treiber...${NC}"
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver python3-venv

# 2. Virtual Environment erstellen
if [ ! -d "venv" ]; then
    echo -e "${GREEN}🐍 Erstelle Python Virtual Environment...${NC}"
    python3 -m venv venv
fi

# 3. Python Pakete installieren
echo -e "${GREEN}📥 Installiere Python-Abhängigkeiten...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. .env Datei Setup
if [ ! -f ".env" ]; then
    echo -e "${GREEN}🔑 Erstelle .env Datei...${NC}"
    echo "Bitte gib deinen Telegram Token ein:"
    read token
    echo "Bitte gib deine Telegram Chat ID ein:"
    read chatid
    
    echo "TELEGRAM_TOKEN=$token" > .env
    echo "TELEGRAM_CHAT_ID=$chatid" >> .env
    echo -e "${GREEN}✅ .env Datei gespeichert!${NC}"
else
    echo -e "${GREEN}ℹ️ .env Datei existiert bereits. Überspringe.${NC}"
fi

# 5. Systemd Service automatisch anlegen
echo -e "${GREEN}⚙️ Richte Autostart (Systemd) ein...${NC}"

# Pfad zum aktuellen Ordner ermitteln
DIR=$(pwd)
USER=$(whoami)

# Service-Datei Inhalt
SERVICE_CONTENT="[Unit]
Description=BM Status Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$DIR
ExecStart=$DIR/venv/bin/python $DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"

# Datei schreiben (braucht sudo)
echo "$SERVICE_CONTENT" | sudo tee /etc/systemd/system/battlemetrics.service > /dev/null

# Service aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable battlemetrics.service
sudo systemctl restart battlemetrics.service

echo -e "${GREEN}✅ Installation abgeschlossen! Der Bot läuft jetzt.${NC}"
echo -e "${GREEN}Log ansehen mit: journalctl -u battlemetrics.service -f${NC}"