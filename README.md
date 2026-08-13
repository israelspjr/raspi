# Jogo Musical Raspberry Pi 5

Jogo offline inspirado em Guitar Hero, com 10 botoeiras e LEDs bicolores. Esta primeira versão usa teclado ou toque para simular o hardware.

## Instalação no Raspberry

O primeiro provisionamento precisa de acesso temporário à internet para o `apt` e o `pip`. Depois da instalação, o jogo funciona totalmente offline. O frontend React já está compilado em `frontend/dist`, portanto Node.js não é necessário no Raspberry.

Após copiar ou clonar o projeto:

```bash
cd raspi-music-game
chmod +x scripts/install_raspberry.sh
./scripts/install_raspberry.sh
```

Abra `http://localhost:8000`. Em outro computador da rede, use `http://IP_DO_RASPBERRY:8000`.

Verificação e logs:

```bash
sudo systemctl status music-game
sudo journalctl -u music-game -f
```

## Teste sem instalar o serviço

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Controles

As teclas `1 2 3 4 5 6 7 8 9 0` representam as dez botoeiras. O backend é a autoridade da rodada e transmite eventos por WebSocket.

## Adicionar música

Copie `songs/demo`, altere o `chart.json` e use tempos em milissegundos. O número do botão vai de `0` a `9`. Um arquivo de áudio poderá ser colocado na mesma pasta e referenciado pelo campo `audio` numa próxima etapa de sincronização.

## Próximas etapas de hardware

1. Confirmar o modelo exato dos LEDs bicolores (ânodo ou cátodo comum).
2. Confirmar botoeiras normalmente abertas e tensão dos LEDs.
3. Definir ligação com dois MCP23017 por I²C.
4. Implementar leitura física em `backend/hardware.py`.
5. Calibrar debounce, latência e janela de acerto no equipamento montado.
