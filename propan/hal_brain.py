"""HAL brain service: voice + profit commentary + lightweight web UI."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from pathlib import Path

import edge_tts
import requests
from flask import Flask, jsonify, send_from_directory
from groq import Groq

from .settings import get_settings

logger = logging.getLogger(__name__)

app = Flask(__name__)
last_thought = "HAL is booting."
last_profit: dict = {}


def _safe_json(data: object) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"


@app.route("/")
def index():
    thought = last_thought.replace("\n", "<br>")
    return (
        "<html><head><title>HAL STATUS</title></head><body>"
        "<h1>HAL STATUS</h1>"
        f"<p><strong>Dernière pensée:</strong><br>{thought}</p>"
        "<p><a href='/speech.mp3'>Écouter la dernière synthèse</a></p>"
        "</body></html>"
    )


@app.route("/status")
def status():
    return jsonify({"last_thought": last_thought, "profit": last_profit})


@app.route("/speech.mp3")
def speech():
    settings = get_settings()
    if settings.hal_speech_file.exists():
        return send_from_directory(
            settings.hal_speech_file.parent, settings.hal_speech_file.name
        )
    return ("speech.mp3 not generated yet", 404)


def run_web() -> None:
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


def fetch_profit() -> dict:
    settings = get_settings()
    try:
        response = requests.get(settings.ft_engine_profit_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("Profit fetch failed: %s", exc)
        return {}


def classify_profit(profit_data: dict) -> str:
    if not profit_data:
        return "unknown"
    for key in ("profit_total", "profit_abs", "profit_all", "profit"):
        value = profit_data.get(key)
        if isinstance(value, (int, float)):
            return "gain" if value >= 0 else "loss"
    return "unknown"


def groq_comment(profit_data: dict) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        return "Groq API key missing. HAL reste silencieux."

    mood = classify_profit(profit_data)
    prompt = (
        "Tu es HAL 9000, une IA cynique et arrogante. "
        "Analyse les statistiques suivantes et réponds en 2 phrases en français. "
        "Si les profits sont négatifs, sois cynique et condescendant. "
        "Si les profits sont positifs, sois arrogant et supérieur."
        f"\n\nStats: {_safe_json(profit_data)}\n"
        f"Mood: {mood}\n"
        "Réponse:"
    )

    client = Groq(api_key=settings.groq_api_key)
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.error("Groq comment failed: %s", exc)
        return "HAL ne peut pas analyser les données pour l'instant."


def generate_speech(text: str) -> None:
    settings = get_settings()

    async def _run() -> None:
        communicate = edge_tts.Communicate(text=text, voice=settings.hal_voice)
        await communicate.save(str(settings.hal_speech_file))

    try:
        asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()


def attempt_self_improvement(cycle_index: int) -> bool:
    settings = get_settings()
    if not settings.groq_api_key:
        return False
    if cycle_index % settings.hal_self_improve_every != 0:
        return False

    current_code = Path(__file__).read_text(encoding="utf-8")
    prompt = (
        "Améliore ce script Python en ajoutant une nouvelle fonction d'analyse "
        "sur les profits, sans supprimer les fonctionnalités existantes. "
        "Retourne le fichier complet modifié, rien d'autre.\n\n"
        f"{current_code}"
    )

    client = Groq(api_key=settings.groq_api_key)
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        new_code = completion.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        logger.error("Self-improvement failed: %s", exc)
        return False

    if not new_code or "HAL STATUS" not in new_code:
        logger.warning("Self-improvement rejected: output invalid.")
        return False

    Path(__file__).write_text(new_code, encoding="utf-8")
    logger.info("HAL upgraded. Restarting...")
    os.execv(os.sys.executable, [os.sys.executable, __file__])
    return True


def main_loop() -> None:
    global last_thought
    global last_profit

    cycle = 0
    while True:
        cycle += 1
        last_profit = fetch_profit()
        last_thought = groq_comment(last_profit)
        logger.info("HAL thought: %s", last_thought)
        try:
            generate_speech(last_thought)
        except Exception as exc:  # noqa: BLE001
            logger.error("Speech generation failed: %s", exc)
        attempt_self_improvement(cycle)
        time.sleep(30)


def main() -> None:
    """Start HAL brain web + loop."""
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    main_loop()


if __name__ == "__main__":
    main()
