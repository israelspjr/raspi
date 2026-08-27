#!/usr/bin/env bash

# Coleta somente leitura para diagnosticar botoeiras e WS2812B no Raspberry Pi 5.

set -u

APP_DIR="${APP_DIR:-/home/user/raspi-music-game}"
SERVICE_NAME="${SERVICE_NAME:-music-game}"
OUTPUT_FILE="${1:-$APP_DIR/diagnostico-hardware.txt}"

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

run_if_available() {
    local command_name="$1"
    shift
    if command -v "$command_name" >/dev/null 2>&1; then
        "$command_name" "$@" || true
    else
        printf 'Comando nÃ£o instalado: %s\n' "$command_name"
    fi
}

touch "$OUTPUT_FILE"
exec > >(tee "$OUTPUT_FILE") 2>&1

section "DATA E IDENTIFICAÃ‡ÃƒO"
date --iso-8601=seconds || date
hostnamectl || true
printf 'Modelo: '
tr -d '\000' </proc/device-tree/model 2>/dev/null || true
printf '\n'
uname -a
dpkg --print-architecture 2>/dev/null || true
cat /etc/os-release 2>/dev/null || true

section "ENERGIA, TEMPERATURA E KERNEL"
run_if_available vcgencmd get_throttled
run_if_available vcgencmd measure_temp
free -h || true
df -h / "$APP_DIR" || true
dmesg --ctime 2>/dev/null \
    | grep -Ei 'spi|gpio|voltage|under.?voltage|thrott|power' \
    | tail -n 150 || true

section "SERVIÃ‡O E API"
systemctl status "$SERVICE_NAME" --no-pager -l || true
systemctl show "$SERVICE_NAME" \
    -p User \
    -p Group \
    -p SupplementaryGroups \
    -p WorkingDirectory \
    -p Environment \
    -p EnvironmentFiles \
    -p ExecStart \
    --no-pager || true
printf '\nResposta de /api/health:\n'
curl --silent --show-error --max-time 5 http://localhost:8000/api/health || true
printf '\n'

section "CONFIGURAÃ‡ÃƒO DO HARDWARE"
if [[ -f /etc/default/music-game ]]; then
    grep -E '^(HARDWARE_MODE|BUTTON_GPIOS_BCM|BUTTON_DEBOUNCE|RING_COUNT|LEDS_PER_RING|SPI_DEVICE|SPI_SPEED_KHZ|LED_BRIGHTNESS)=' \
        /etc/default/music-game || true
else
    printf '/etc/default/music-game nÃ£o encontrado.\n'
fi

section "LOGS DO SERVIÃ‡O"
journalctl -u "$SERVICE_NAME" -n 180 --no-pager -o short-iso || true

section "USUÃRIO, GRUPOS E PERMISSÃ•ES"
id user 2>/dev/null || true
getent group gpio 2>/dev/null || true
getent group spi 2>/dev/null || true
namei -l "$APP_DIR" 2>/dev/null || true
ls -ld "$APP_DIR" "$APP_DIR/.venv" 2>/dev/null || true
find "$APP_DIR" -maxdepth 1 -name '.lgd-nfy*' -ls 2>/dev/null || true

section "DISPOSITIVOS GPIO E SPI"
ls -l /dev/gpiochip* /dev/gpiomem* /dev/spidev* 2>&1 || true
ls -l /sys/class/spidev 2>&1 || true
for device in /sys/class/spidev/spidev*; do
    [[ -e "$device" ]] || continue
    printf '%s -> %s\n' "$device" "$(readlink -f "$device")"
done
run_if_available raspi-config nonint get_spi
grep -HnE '^[[:space:]]*(dtparam=spi|dtoverlay=.*spi)' \
    /boot/firmware/config.txt /boot/config.txt 2>/dev/null || true
lsmod | grep -Ei '(^|_)spi|gpio' || true

section "PROCESSOS USANDO GPIO/SPI"
pgrep -af 'uvicorn|test-hardware|test_hardware_loop|lgpio|pigpio' || true
run_if_available fuser -v /dev/gpiochip0 /dev/spidev0.0

section "ESTADO DOS PINOS BCM"
if command -v pinctrl >/dev/null 2>&1; then
    for gpio in 5 6 10 12 16 17 18 22 25 26 27; do
        pinctrl get "$gpio" || true
    done
else
    printf 'Comando pinctrl nÃ£o instalado.\n'
fi

section "INFORMAÃ‡Ã•ES DO GPIOCHIP"
if command -v gpioinfo >/dev/null 2>&1; then
    gpioinfo gpiochip0 || gpioinfo /dev/gpiochip0 || true
else
    printf 'Comando gpioinfo nÃ£o instalado.\n'
fi

section "VERSÃ•ES PYTHON DO PROJETO"
if [[ -x "$APP_DIR/.venv/bin/python" ]]; then
    sudo -u user "$APP_DIR/.venv/bin/python" - <<'PY' || true
import importlib.metadata
import platform
import sys

print("ExecutÃ¡vel:", sys.executable)
print("Python:", platform.python_version())
print("Plataforma:", platform.platform())

for package in (
    "fastapi",
    "uvicorn",
    "numpy",
    "gpiozero",
    "lgpio",
    "spidev",
    "Pi5Neo",
):
    try:
        print(f"{package}: {importlib.metadata.version(package)}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package}: NÃƒO INSTALADO")
PY
else
    printf 'Python do ambiente virtual nÃ£o encontrado.\n'
fi

section "ARQUIVOS PRINCIPAIS"
sha256sum \
    "$APP_DIR/backend/hardware.py" \
    "$APP_DIR/backend/main.py" \
    "$APP_DIR/test-hardware.py" \
    "$APP_DIR/scripts/test_hardware_loop.py" \
    2>/dev/null || true

section "FIM"
printf 'DiagnÃ³stico salvo em: %s\n' "$OUTPUT_FILE"
