"""API routes for the HAL brain web app."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from flask import Blueprint, Response, current_app, jsonify, send_from_directory

if TYPE_CHECKING:
    from .app import AppState

api_bp = Blueprint("api", __name__)


def _get_state() -> AppState:
    return current_app.extensions["state"]


def _segment_text(text: str, max_len: int = 160) -> list[str]:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return []
    raw_segments = re.split(r"(?<=[.!?…])\s+", cleaned)
    segments: list[str] = []
    for segment in raw_segments:
        if not segment:
            continue
        if len(segment) <= max_len:
            segments.append(segment)
            continue
        words = segment.split()
        buffer: list[str] = []
        for word in words:
            candidate = " ".join(buffer + [word])
            if len(candidate) > max_len and buffer:
                segments.append(" ".join(buffer))
                buffer = [word]
            else:
                buffer.append(word)
        if buffer:
            segments.append(" ".join(buffer))
    return segments


@api_bp.route("/api/health")
def health() -> Response:
    """Return a health snapshot for UI consumption."""
    state = _get_state()
    issues: list[str] = []

    if state.last_profit_error:
        issues.append(state.last_profit_error)
    if state.last_commentary_error:
        issues.append(state.last_commentary_error)
    if state.last_audio_error:
        issues.append(state.last_audio_error)

    audio_file = state.settings.hal_speech_file
    audio_available = audio_file.exists()
    thought_segments = _segment_text(state.last_commentary or "")
    latest_thought = state.thought_store.latest()

    data = {
        "status": "ok",
        "last_thought": state.last_commentary,
        "thought": {
            "text": state.last_commentary,
            "segments": thought_segments,
            "status": state.last_commentary_status,
            "source": latest_thought["source"] if latest_thought else "system",
            "last_error": state.last_commentary_error,
            "last_update": state.last_commentary_at,
        },
        "profit": {
            "status": state.last_profit_status,
            "last_error": state.last_profit_error,
            "last_update": state.last_profit_at,
        },
        "groq": {
            "status": state.last_commentary_status,
            "last_error": state.last_commentary_error,
            "last_update": state.last_commentary_at,
        },
        "audio": {
            "status": state.last_audio_status,
            "last_error": state.last_audio_error,
            "last_update": state.last_audio_at,
            "available": audio_available,
            "url": "/speech.mp3" if audio_available else None,
        },
        "voice": {
            "status": state.last_audio_status,
            "last_error": state.last_audio_error,
            "last_update": state.last_audio_at,
            "available": audio_available,
        },
        "issues": issues,
        "settings": {
            "ft_engine_profit_url": state.settings.ft_engine_profit_url,
            "hal_voice": state.settings.hal_voice,
            "hal_speech_file": str(state.settings.hal_speech_file),
            "hal_thought_interval": state.settings.hal_thought_interval,
            "log_level": state.settings.log_level,
            "groq_api_key_present": bool(state.settings.groq_api_key),
            "hal_self_improve": state.settings.hal_self_improve,
        },
    }
    return jsonify(data)


@api_bp.route("/api/profit")
def profit() -> Response:
    """Return the latest profit data."""
    state = _get_state()
    if not state.last_profit_at:
        result = state.profit_service.fetch()
        state.touch_profit(result.status, result.data, result.error)
    return jsonify(
        {
            "status": state.last_profit_status,
            "data": state.last_profit,
            "error": state.last_profit_error,
            "last_update": state.last_profit_at,
        }
    )


@api_bp.route("/api/thoughts")
def thoughts() -> Response:
    """Return thought history."""
    state = _get_state()
    items = state.thought_store.list()
    return jsonify(
        {
            "items": items,
            "count": len(items),
        }
    )


@api_bp.route("/api/thoughts/clear", methods=["POST"])
def clear_thoughts() -> Response:
    """Clear thought history."""
    state = _get_state()
    state.thought_store.clear()
    return jsonify({"status": "cleared"})


@api_bp.route("/api/audio")
def audio_status() -> Response:
    """Return audio availability information."""
    state = _get_state()
    audio_file = state.settings.hal_speech_file
    available = audio_file.exists()
    return jsonify(
        {
            "available": available,
            "url": "/speech.mp3" if available else None,
            "last_update": state.last_audio_at,
            "status": state.last_audio_status,
            "last_error": state.last_audio_error,
        }
    )


@api_bp.route("/speech.mp3")
def speech_file() -> Response:
    """Serve the latest speech file if present."""
    state = _get_state()
    audio_file = state.settings.hal_speech_file
    if audio_file.exists():
        return send_from_directory(audio_file.parent, audio_file.name)
    return Response(status=204)


@api_bp.route("/favicon.ico")
def favicon() -> Response:
    """Avoid 404s for missing favicons."""
    return Response(status=204)
