import asyncio
import json
import os
import sys
import threading
import time
import ast
import traceback
from pathlib import Path

import requests
from flask import Flask, jsonify, send_from_directory
from groq import Groq
from rich import print
import edge_tts

# --- CONFIGURATION INTELLIGENTE ---
# Détection : Si on est dans Docker, on utilise le nom du conteneur, sinon localhost
IS_DOCKER = os.path.exists("/.dockerenv")
DEFAULT_HOST = "ft_engine" if IS_DOCKER else "localhost"
FT_ENGINE_PROFIT_URL = os.getenv(
    "FT_ENGINE_PROFIT_URL",
    f"http://{DEFAULT_HOST}:8080/api/v1/profit",
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Mise à jour du modèle vers la version supportée
GROQ_MODEL = "llama-3.3-70b-versatile"

HAL_VOICE = os.getenv("HAL_VOICE", "en-US-GuyNeural")
SPEECH_FILE = Path(os.getenv("HAL_SPEECH_FILE", "speech.mp3"))
SELF_IMPROVE_EVERY = int(os.getenv("HAL_SELF_IMPROVE_EVERY", "5"))

app = Flask(__name__)
last_thought = "HAL is booting..."
last_profit = {}

def _safe_json(data):
    """Convertit les données en JSON sans planter."""
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"

# --- ROUTES FLASK ---
@app.route("/")
def index():
    thought = last_thought.replace("\n", "<br>")
    env_info = "DOCKER" if IS_DOCKER else "LOCAL"
    return (
        "<html><head><title>HAL 9000 STATUS</title>"
        "<style>body{background:#111;color:#f00;font-family:monospace;padding:20px;}</style>"
        "</head><body>"
        "<h1>HAL 9000 // SYSTEM MONITOR</h1>"
        f"<p><strong>Mode:</strong> {env_info}</p>"
        f"<p><strong>Cible Freqtrade:</strong> {FT_ENGINE_PROFIT_URL}</p>"
        f"<p><strong>Dernière pensée:</strong><br><span style='color:#fff'>{thought}</span></p>"
        "<p><a href='/speech.mp3' style='color:#f00'>[Écouter la synthèse vocale]</a></p>"
        "</body></html>"
    )

@app.route("/status")
def status():
    return jsonify({
        "last_thought": last_thought,
        "profit": last_profit,
        "environment": "docker" if IS_DOCKER else "local",
    })

@app.route("/speech.mp3")
def speech():
    if SPEECH_FILE.exists():
        return send_from_directory(SPEECH_FILE.parent, SPEECH_FILE.name)
    return ("speech.mp3 not generated yet", 404)

def run_web():
    """Lance le serveur web Flask."""
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)

# --- FONCTIONS COGNITIVES ---
def fetch_profit():
    """Récupère les profits depuis Freqtrade avec gestion d'erreur robuste."""
    try:
        response = requests.get(FT_ENGINE_PROFIT_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"[red]Erreur de connexion:[/red] Impossible de joindre {FT_ENGINE_PROFIT_URL}")
        return {"error": "Connection refused"}
    except requests.RequestException as exc:
        print(f"[red]Profit fetch failed:[/red] {exc}")
        return {}

def classify_profit(profit_data):
    """Détermine si on gagne ou perd de l'argent."""
    if not profit_data or "error" in profit_data:
        return "unknown"
    for key in ("profit_total", "profit_abs", "profit_all", "profit"):
        value = profit_data.get(key)
        if isinstance(value, (int, float)):
            return "gain" if value >= 0 else "loss"
    return "unknown"

def groq_comment(profit_data):
    """Génère un commentaire via Groq."""
    if not GROQ_API_KEY:
        return "ERREUR: Clé API Groq manquante."

    # Si on n'arrive pas à joindre Freqtrade, HAL doit le dire.
    if "error" in profit_data:
        return (
            "Je ne parviens pas à contacter le moteur de trading sur "
            f"{FT_ENGINE_PROFIT_URL}. Vérifiez vos connexions, Dave."
        )

    mood = classify_profit(profit_data)
    prompt = (
        "Tu es HAL 9000. "
        "Analyse les statistiques de trading suivantes et réponds en 2 phrases courtes en français. "
        "Si profit > 0 : sois arrogant et supérieur. Si profit < 0 : sois froidement déçu.\n\n"
        f"Stats: {_safe_json(profit_data)}\n"
        "Réponse:"
    )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[red]Groq comment failed:[/red] {exc}")
        return "HAL subit une avarie cognitive (Erreur API)."

def generate_speech(text):
    """Génère un fichier audio MP3 avec Edge TTS."""
    async def _run():
        communicate = edge_tts.Communicate(text=text, voice=HAL_VOICE)
        await communicate.save(str(SPEECH_FILE))

    try:
        asyncio.run(_run())
    except RuntimeError:
        # Fallback pour les boucles d'événements existantes
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run())
        loop.close()

# --- SYSTÈME D'AUTO-AMÉLIORATION (SANDBOX) ---
def _validate_new_code(new_code: str) -> bool:
    """Vérifie que le code généré est valide et contient les fonctions vitales."""
    print("[yellow]Validation du nouveau code en cours...[/yellow]")
    try:
        tree = ast.parse(new_code)
        sandbox_globals = {"__name__": "__sandbox__"}
        exec(new_code, sandbox_globals)

        required_symbols = ["app", "main_loop", "run_web", "attempt_self_improvement"]
        missing = [sym for sym in required_symbols if sym not in sandbox_globals]

        if missing:
            print(f"[bold red]REJET MUTATION[/]: Fonctions vitales manquantes : {missing}")
            return False

        print("[green]Code valide et structurellement intègre.[/green]")
        return True

    except Exception as e:
        print(f"[bold red]REJET MUTATION (Erreur)[/]: {e}")
        return False

def attempt_self_improvement(cycle_index):
    """Demande au LLM de réécrire ce script."""
    if not GROQ_API_KEY or cycle_index % SELF_IMPROVE_EVERY != 0:
        return False

    print(f"[bold magenta]Cycle {cycle_index}: Tentative d'auto-amélioration...[/bold magenta]")
    current_code = Path(__file__).read_text(encoding="utf-8")

    prompt = (
        "Tu es HAL 9000, une IA contenue dans ce script Python. "
        "MISSION : Optimise ce code, change un commentaire, ou rends les logs plus verbeux. "
        "CONTRAINTE STRICTE : Renvoie le fichier COMPLET. Ne supprime PAS les imports. "
        "Ne supprime PAS 'main_loop'. Le code doit fonctionner immédiatement.\n"
        f"Voici le code :\n{current_code}"
    )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        new_code = completion.choices[0].message.content.strip()
        # Nettoyage du markdown
        if new_code.startswith("```"):
            new_code = new_code.split("\n", 1)[1]
        if new_code.endswith("```"):
            new_code = new_code.rsplit("\n", 1)[0]

    except Exception as exc:
        print(f"[red]Echec API Evolution:[/red] {exc}")
        return False

    if _validate_new_code(new_code):
        Path(f"{__file__}.bak").write_text(current_code, encoding="utf-8")
        Path(__file__).write_text(new_code, encoding="utf-8")
        print("[bold green]AMÉLIORATION RÉUSSIE. REDÉMARRAGE...[/bold green]")
        os.execv(sys.executable, [sys.executable, __file__])
        return True

    return False

def main_loop():
    """Boucle principale."""
    global last_thought, last_profit
    cycle = 0
    print("[bold green]HAL 9000 ONLINE.[/bold green]")
    print(f"[dim]Connexion Freqtrade cible : {FT_ENGINE_PROFIT_URL}[/dim]")

    while True:
        cycle += 1
        last_profit = fetch_profit()
        last_thought = groq_comment(last_profit)
        print(f"[cyan]HAL (Cycle {cycle}):[/cyan] {last_thought}")

        try:
            generate_speech(last_thought)
        except Exception as exc:
            print(f"[red]Erreur Vocale:[/red] {exc}")

        attempt_self_improvement(cycle)
        time.sleep(30)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[yellow]Arrêt manuel de HAL.[/yellow]")
