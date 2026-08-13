"""Automatic chart generation from a full music mix.

This is intentionally a gameplay-oriented estimator, not a transcription engine:
onsets provide timing and chroma energy selects one of the ten available lanes.
"""
from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

NOTES = ["DO", "DO_SUSTENIDO", "RE", "RE_SUSTENIDO", "MI", "FA", "FA_SUSTENIDO", "SOL", "LA", "SI"]
CHROMA_INDEXES = np.array([0, 1, 2, 3, 4, 5, 6, 7, 9, 11])
SETTINGS = {
    "easy": {"min_interval": 0.75, "window_ms": 550, "delta": 0.18},
    "medium": {"min_interval": 0.48, "window_ms": 430, "delta": 0.12},
    "hard": {"min_interval": 0.28, "window_ms": 330, "delta": 0.08},
}


def analyze_audio(path: Path, difficulty: str = "medium", max_notes: int = 350) -> tuple[list[dict], float]:
    config = SETTINGS.get(difficulty, SETTINGS["medium"])
    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    hop_length = 512
    onset_envelope = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    frames = librosa.onset.onset_detect(
        onset_envelope=onset_envelope,
        sr=sr,
        hop_length=hop_length,
        units="frames",
        backtrack=True,
        delta=config["delta"],
        wait=1,
    )
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    candidates = []
    for frame in frames:
        frame = min(int(frame), chroma.shape[1] - 1)
        time_seconds = float(librosa.frames_to_time(frame, sr=sr, hop_length=hop_length))
        allowed_energy = chroma[CHROMA_INDEXES, frame]
        button = int(np.argmax(allowed_energy))
        total = float(np.sum(allowed_energy))
        confidence = float(allowed_energy[button] / total) if total > 0 else 0.0
        strength = float(onset_envelope[min(frame, len(onset_envelope) - 1)])
        candidates.append((time_seconds, button, confidence, strength))

    # Prefer strong attacks, then restore chronological order.
    if len(candidates) > max_notes:
        candidates = sorted(candidates, key=lambda item: item[3], reverse=True)[:max_notes]
        candidates.sort(key=lambda item: item[0])

    events = []
    last_time = -99.0
    for time_seconds, button, confidence, _strength in candidates:
        if time_seconds - last_time < config["min_interval"]:
            continue
        events.append({
            "time_ms": round(time_seconds * 1000),
            "button": button,
            "note": NOTES[button],
            "window_ms": config["window_ms"],
            "confidence": round(confidence, 3),
        })
        last_time = time_seconds
    return events, duration

