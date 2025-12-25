import asyncio
import json
import os
import threading
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, send_from_directory
from groq import Groq
from rich import print
import edge_tts

FT_ENGINE_PROFIT_URL = os.getenv("FT_ENGINE_PROFIT_URL", "http://ft_engine:8080/api/v1/profit")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HAL_VOICE = os.getenv("HAL_VOICE", "en-US-GuyNeural")
SPEECH_FILE = Path(os.getenv("HAL_SPEECH_FILE", "speech.mp3"))
SELF_IMPROVE_EVERY = int(os.getenv("HAL_SELF_IMPROVE_EVERY", "5"))

app = Flask(__name__)
last_thought = "HAL is booting."
last_profit = {}


def _safe_json(data):
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
    if SPEECH_FILE.exists():
        return send_from_directory(SPEECH_FILE.parent, SPEECH_FILE.name)
    return ("speech.mp3 not generated yet", 404)


def run_web():
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


def fetch_profit():
    try:
        response = requests.get(FT_ENGINE_PROFIT_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"[red]Profit fetch failed:[/red] {exc}")
        return {}


def classify_profit(profit_data):
    if not profit_data:
        return "unknown"
    for key in ("profit_total", "profit_abs", "profit_all", "profit"):
        value = profit_data.get(key)
        if isinstance(value, (int, float)):
            return "gain" if value >= 0 else "loss"
    return "unknown"


def groq_comment(profit_data):
    if not GROQ_API_KEY:
        return "Groq API key missing. HAL reste silencieux."

    mood = classify_profit(profit_data)
    prompt = (
        "Tu es HAL 9000, une IA cynique et arrogante. "
        "Analyse les statistiques suivantes et réponds en 2 phrases en français. "
        "Si les profits sont négatifs, sois cynique et condescendant. "
        "Si les profits sont positifs, sois arrogant et supérieur.\n\n"
        f"Stats: {_safe_json(profit_data)}\n"
        "Réponse:"
    )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001
        print(f"[red]Groq comment failed:[/red] {exc}")
        return "HAL ne peut pas analyser les données pour l'instant."


def generate_speech(text):
    async def _run():
        communicate = edge_tts.Communicate(text=text, voice=HAL_VOICE)
        await communicate.save(str(SPEECH_FILE))

    try:
        asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()


def attempt_self_improvement(cycle_index):
    if not GROQ_API_KEY:
        return False
    if cycle_index % SELF_IMPROVE_EVERY != 0:
        return False

    current_code = Path(__file__).read_text(encoding="utf-8")
    prompt = (
        "Améliore ce script Python en ajoutant une nouvelle fonction d'analyse "
        "sur les profits, sans supprimer les fonctionnalités existantes. "
        "Retourne le fichier complet modifié, rien d'autre.\n\n"
        f"{current_code}"
    )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        new_code = completion.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        print(f"[red]Self-improvement failed:[/red] {exc}")
        return False

    if not new_code or "HAL STATUS" not in new_code:
        print("[yellow]Self-improvement rejected: output invalid.[/yellow]")
        return False

    Path(__file__).write_text(new_code, encoding="utf-8")
    print("[green]HAL upgraded. Restarting...[/green]")
    os.execv(os.sys.executable, [os.sys.executable, __file__])
    return True


def main_loop():
    global last_thought
    global last_profit

    cycle = 0
    while True:
        cycle += 1
        last_profit = fetch_profit()
        last_thought = groq_comment(last_profit)
        print(f"[cyan]HAL thought:[/cyan] {last_thought}")
        try:
            generate_speech(last_thought)
        except Exception as exc:  # noqa: BLE001
            print(f"[red]Speech generation failed:[/red] {exc}")
        attempt_self_improvement(cycle)
        time.sleep(30)


if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    main_loop()
