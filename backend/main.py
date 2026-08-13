from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .game import GameEngine

ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT / "songs"
WEB = ROOT / "frontend" / "dist"

app = FastAPI(title="Jogo Musical Raspberry")
clients: set[WebSocket] = set()


def load_songs() -> list[dict]:
    found = []
    for chart in sorted(SONGS.glob("*/chart.json")):
        data = json.loads(chart.read_text(encoding="utf-8"))
        data["event_count"] = len(data.get("events", []))
        found.append(data)
    return found


async def broadcast(message: dict) -> None:
    dead = []
    for client in clients:
        try:
            await client.send_json(message)
        except Exception:
            dead.append(client)
    clients.difference_update(dead)


engine = GameEngine(broadcast)


@app.get("/api/health")
def health():
    return {"ok": True, "mode": "simulator"}


@app.get("/api/songs")
def songs():
    return [{k: v for k, v in song.items() if k != "events"} for song in load_songs()]


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    await ws.send_json({"type": "ready"})
    try:
        while True:
            message = await ws.receive_json()
            if message.get("type") == "start":
                song = next((s for s in load_songs() if s["id"] == message.get("song")), None)
                if song:
                    await engine.start(song)
            elif message.get("type") == "press":
                await engine.press(int(message["button"]))
            elif message.get("type") == "stop":
                await engine.stop()
                await broadcast({"type": "stopped"})
    except WebSocketDisconnect:
        clients.discard(ws)


app.mount("/songs", StaticFiles(directory=SONGS), name="songs")
app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/{path:path}")
def spa(path: str):
    target = WEB / path
    return FileResponse(target if target.is_file() else WEB / "index.html")

