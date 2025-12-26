# propan

> HAL et Ouroboros ont décidé d'arrêter de bricoler dans le cockpit. Voici une base propre, prête pour une interface immersive à la Nostromo.

## Vue d'ensemble

`propan` est un projet IA expérimental qui unifie HAL dans une interface web immersive (une seule page) et un CLI propre. Le but est d'avoir un démarrage clair, des diagnostics fiables, et une UI cohérente, en local comme en Docker.

### Documentation

- `docs/ARCHITECTURE.md` : flux, modules, API.
- `docs/INTERFACE.md` : description détaillée de l'UI et des onglets.
- `docs/CONFIGURATION.md` : variables d'environnement et réglages UI.

## Démarrage rapide (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# Optionnel pour contribuer
pip install -e ".[dev]"
```

Copiez `.env.example` en `.env` et ajustez les variables nécessaires.

```bash
python -m propan --help
propan doctor
propan run hal-brain
```

L'interface HAL est disponible sur `http://localhost:9000`.

## Démarrage rapide (Docker)

```bash
docker compose up --build
```

Le service `propan` expose l'UI sur `http://localhost:9000`.

### Développement (avec volume mount)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Interface HAL (web)

- **Une seule page** `/` avec onglets : **STATUT**, **PENSÉES**, **DONNÉES**, **AUDIO**, **RÉGLAGES**, **JOURNAL**.
- Style rétro-futuriste sobre, typographie lisible, rythme volontairement lent.
- **Synchronisation texte/voix** : les réponses HAL s'affichent progressivement pendant la lecture audio.
- **Réglages persistants** (localStorage) : voix ON/OFF, son notification ON/OFF, vitesse de parole, vitesse d'affichage texte.
- L'interface fonctionne sans audio ; **Audio OFF = silence total**.

## Configuration (.env)

Créez un fichier `.env` à la racine (un exemple est fourni dans `.env.example`).

Exemple minimal :

```bash
GROQ_API_KEY=sk-...
HAL_SELF_IMPROVE=false
LOG_LEVEL=INFO
```

| Variable | Description | Défaut |
| --- | --- | --- |
| `GROQ_API_KEY` | Clé API Groq pour HAL/Ouroboros | `None` |
| `FT_ENGINE_PROFIT_URL` | Endpoint profits Freqtrade | `http://ft_engine:8080/api/v1/profit` |
| `HAL_VOICE` | Voix Edge TTS (FR par défaut) | `fr-FR-HenriNeural` |
| `HAL_SPEECH_FILE` | Fichier audio généré | `speech.mp3` |
| `HAL_THOUGHT_INTERVAL` | Intervalle de rafraîchissement HAL (s) | `30` |
| `HAL_SELF_IMPROVE` | Autorise l'auto-amélioration HAL | `false` |
| `HAL_SELF_IMPROVE_EVERY` | Fréquence d'auto-amélioration | `5` |
| `HAL_CYCLE` | Cycle HAL actuel | `1` |
| `LOG_LEVEL` | Niveau de logs | `INFO` |
| `PYTHON_EXECUTABLE` | Exécutable Python utilisé pour relancer | `python3` |

## API HAL Brain

Endpoints principaux :

- `GET /api/health` : état consolidé + segments de texte + audio disponible.
- `GET /api/profit` : snapshot profit.
- `GET /api/thoughts` + `POST /api/thoughts/clear` : historique HAL.
- `GET /api/audio` : disponibilité audio et état TTS.
- `GET /speech.mp3` : MP3 actuel (204 si absent, jamais de 404).

## CLI

Commandes principales :

- `propan run hal` : lance HAL (TUI).
- `propan run ouroboros` : lance le cycle Ouroboros.
- `propan run hal-brain` : lance HAL brain (web + voix).
- `propan dashboard` : dashboard HAL brain.
- `propan doctor` : diagnostics de l'installation (Groq, profit, voix).

## Dépannage rapide

- **`GROQ_API_KEY` manquante** : HAL/Ouroboros ne mutent pas. Ajoutez la clé dans `.env`.
- **Groq 401** : vérifiez la clé API et relancez `propan doctor`.
- **HAL brain ne voit pas Freqtrade** : vérifiez `FT_ENGINE_PROFIT_URL` et le réseau Docker/local.
- **Voix absente** : vérifiez `edge-tts` et la voix `HAL_VOICE`.
- **Audio OFF** : activez la voix dans l'onglet RÉGLAGES.

## Tests

```bash
pytest
```

---

HAL affirme que tout est sous contrôle. Ouroboros, lui, préfère rester mystérieux.
