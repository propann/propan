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

# --- CONFIGURATION ---
FT_ENGINE_PROFIT_URL = os.getenv("FT_ENGINE_PROFIT_URL", "http://ft_engine:8080/api/v1/profit")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HAL_VOICE = os.getenv("HAL_VOICE", "en-US-GuyNeural")
SPEECH_FILE = Path(os.getenv("HAL_SPEECH_FILE", "speech.mp3"))
# On tente une amélioration tous les X cycles de boucle
SELF_IMPROVE_EVERY = int(os.getenv("HAL_SELF_IMPROVE_EVERY", "5"))

app = Flask(__name__)
last_thought = "HAL is booting."
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
    """Lance le serveur web Flask."""
    # use_reloader=False est CRUCIAL car nous gérons nous-mêmes le redémarrage
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


# --- FONCTIONS COGNITIVES ---
def fetch_profit():
    """Récupère les profits depuis Freqtrade."""
    try:
        response = requests.get(FT_ENGINE_PROFIT_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"[red]Profit fetch failed:[/red] {exc}")
        return {}


def classify_profit(profit_data):
    """Détermine si on gagne ou perd de l'argent."""
    if not profit_data:
        return "unknown"
    for key in ("profit_total", "profit_abs", "profit_all", "profit"):
        value = profit_data.get(key)
        if isinstance(value, (int, float)):
            return "gain" if value >= 0 else "loss"
    return "unknown"


def groq_comment(profit_data):
    """Génère un commentaire via Groq."""
    if not GROQ_API_KEY:
        return "Groq API key missing. HAL reste silencieux."

    mood = classify_profit(profit_data)
    prompt = (
        "Tu es HAL 9000. "
        "Analyse les statistiques suivantes et réponds en 2 phrases courtes en français. "
        "Si profit > 0 : sois arrogant. Si profit < 0 : sois déçu/cynique.\n\n"
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
    except Exception as exc:
        print(f"[red]Groq comment failed:[/red] {exc}")
        return "HAL ne peut pas analyser les données pour l'instant."


def generate_speech(text):
    """Génère un fichier audio MP3 avec Edge TTS."""

    async def _run():
        communicate = edge_tts.Communicate(text=text, voice=HAL_VOICE)
        await communicate.save(str(SPEECH_FILE))

    try:
        asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()


# --- SYSTÈME D'AUTO-AMÉLIORATION (SANDBOX) ---

def _validate_new_code(new_code: str) -> bool:
    """
    Vérifie que le code généré est valide et contient les fonctions vitales.
    Ne l'exécute PAS entièrement, mais charge les définitions en mémoire isolée.
    """
    print("[yellow]Validation du nouveau code en cours...[/yellow]")
    try:
        # 1. Vérification Syntaxique (AST)
        tree = ast.parse(new_code)

        # 2. Vérification structurelle (Présence des composants clés)
        # On exécute le code dans un dictionnaire vide pour voir s'il définit bien les fonctions
        # On force __name__ != "__main__" pour éviter de lancer la boucle infinie pendant le test
        sandbox_globals = {"__name__": "__sandbox__"}
        exec(new_code, sandbox_globals)

        # Liste des symboles qui DOIVENT exister pour que le script marche
        required_symbols = ["app", "main_loop", "run_web", "attempt_self_improvement"]

        missing = [sym for sym in required_symbols if sym not in sandbox_globals]

        if missing:
            print(
                f"[bold red]REJET MUTATION[/]: Le code généré a perdu ces éléments vitaux : {missing}"
            )
            return False

        print("[green]Code valide et structurellement intègre.[/green]")
        return True

    except SyntaxError as e:
        print(f"[bold red]REJET MUTATION (Syntaxe)[/]: {e}")
        return False
    except Exception as e:
        print("[bold red]REJET MUTATION (Runtime Test)[/]:")
        traceback.print_exc()
        return False


def attempt_self_improvement(cycle_index):
    """Demande au LLM de réécrire ce script."""
    if not GROQ_API_KEY:
        return False
    # On ne tente l'amélioration que tous les N cycles pour pas spammer l'API
    if cycle_index % SELF_IMPROVE_EVERY != 0:
        return False

    print(
        f"[bold magenta]Cycle {cycle_index}: Tentative d'auto-amélioration...[/bold magenta]"
    )

    current_code = Path(__file__).read_text(encoding="utf-8")

    # Prompt plus strict pour éviter que HAL ne se casse lui-même
    prompt = (
        "Tu es un système d'IA autonome (HAL) contenu dans un script Python."
        "TA MISSION : Améliore ce code source. Tu peux optimiser une fonction, "
        "changer le ton des commentaires, ou ajouter une petite feature d'analyse."
        "\n\n"
        "RÈGLES IMPÉRATIVES :\n"
        "1. RENVOIE LE CODE COMPLET DU FICHIER. Pas de markdown, juste le code.\n"
        "2. NE SUPPRIME PAS les imports existants (Flask, threading, etc).\n"
        "3. NE SUPPRIME PAS la fonction 'main_loop' ni les routes Flask.\n"
        "4. Le code doit être exécutable immédiatement.\n"
        "\n"
        f"Voici le code actuel :\n{current_code}"
    )

    client = Groq(api_key=GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Température basse pour limiter le chaos
        )
        new_code = completion.choices[0].message.content.strip()

        # Nettoyage si le LLM met des balises markdown ```python
        if new_code.startswith("```"):
            new_code = new_code.split("\n", 1)[1]
        if new_code.endswith("```"):
            new_code = new_code.rsplit("\n", 1)[0]

    except Exception as exc:
        print(f"[red]Self-improvement API call failed:[/red] {exc}")
        return False

    # Validation Sandbox
    if _validate_new_code(new_code):
        # Sauvegarde Backup
        backup_path = Path(f"{__file__}.bak")
        backup_path.write_text(current_code, encoding="utf-8")

        # Écriture nouveau code
        Path(__file__).write_text(new_code, encoding="utf-8")
        print("[bold green]HAL UPGRADED. REBOOTING SYSTEM...[/bold green]")

        # Redémarrage propre
        os.execv(sys.executable, [sys.executable, __file__])
        return True

    return False


def main_loop():
    """Boucle principale de l'IA (Thread principal)."""
    global last_thought
    global last_profit

    cycle = 0
    print("[bold green]HAL 9000 ONLINE.[/bold green]")

    while True:
        cycle += 1

        # 1. Perception
        last_profit = fetch_profit()

        # 2. Réflexion
        last_thought = groq_comment(last_profit)
        print(f"[cyan]HAL thought (Cycle {cycle}):[/cyan] {last_thought}")

        # 3. Expression
        try:
            generate_speech(last_thought)
        except Exception as exc:
            print(f"[red]Speech generation failed:[/red] {exc}")

        # 4. Évolution
        attempt_self_improvement(cycle)

        time.sleep(30)


if __name__ == "__main__":
    # Lancement du serveur Web dans un thread séparé
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    # Lancement de la boucle principale
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[yellow]Arrêt manuel de HAL.[/yellow]")
