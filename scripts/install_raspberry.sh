#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-$USER}"

sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

sed -e "s|__APP_DIR__|$APP_DIR|g" -e "s|__USER__|$SERVICE_USER|g" \
  "$APP_DIR/systemd/music-game.service.template" | sudo tee /etc/systemd/system/music-game.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now music-game

echo "Instalação concluída. Abra http://localhost:8000 ou http://$(hostname -I | awk '{print $1}'):8000"

