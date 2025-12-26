# propan

> HAL et Ouroboros ont décidé d'arrêter de bricoler dans le cockpit. Voici une base propre, mais toujours prête pour les expériences folles.

## Présentation

`propan` est un projet IA expérimental. L'objectif est de garder la flexibilité des scripts d'origine, tout en fournissant une structure claire, un CLI et un démarrage propre (local ou Docker).

## Ce que contient le dépôt

- `propan/` : package Python (HAL, Ouroboros, dashboard, brain web)
- `hal.py`, `hal_brain.py`, `hal_dashboard.py`, `ouroboros.py` : wrappers rétro-compatibles
- `Dockerfile`, `docker-compose.yml` : exécution Docker/Compose

## Installation (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Démarrage rapide (local)

```bash
python -m propan --help
propan doctor
propan run ouroboros
propan run hal
propan run hal-brain
propan dashboard
```

## Démarrage rapide (Docker)

```bash
docker compose up --build
```

Le service `propan` expose le dashboard web HAL Brain sur `http://localhost:9000`.

## CLI

Commandes principales :

- `propan run ouroboros`
- `propan run hal`
- `propan run hal-brain`
- `propan dashboard`
- `propan doctor`

## Variables d'environnement

| Variable | Description | Défaut |
| --- | --- | --- |
| `GROQ_API_KEY` | Clé API Groq pour HAL/Ouroboros | `None` |
| `FT_ENGINE_PROFIT_URL` | Endpoint profits Freqtrade | `http://ft_engine:8080/api/v1/profit` |
| `HAL_VOICE` | Voix pour la synthèse vocale | `en-US-GuyNeural` |
| `HAL_SPEECH_FILE` | Fichier audio généré | `speech.mp3` |
| `HAL_SELF_IMPROVE_EVERY` | Fréquence d'auto-amélioration | `5` |
| `HAL_CYCLE` | Cycle HAL actuel | `1` |
| `LOG_LEVEL` | Niveau de logs | `INFO` |
| `PYTHON_EXECUTABLE` | Exécutable Python utilisé pour relancer | `python3` |

Charge automatiquement un `.env` si présent.

## Compatibilité scripts historiques

Les anciens fichiers racine (`hal.py`, `ouroboros.py`, etc.) restent exécutables et appellent le package `propan`.

## Troubleshooting

- **`GROQ_API_KEY` manquant** : HAL/Ouroboros ne mutent pas. Ajoutez la clé dans `.env`.
- **HAL brain ne voit pas Freqtrade** : vérifiez `FT_ENGINE_PROFIT_URL` et le réseau Docker.
- **TUI muette** : lancez `propan doctor` pour un diagnostic rapide.

## Tests

```bash
pytest
```

---

HAL affirme que tout est sous contrôle. Ouroboros, lui, préfère rester mystérieux.
