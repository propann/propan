# Configuration HAL

## Fichier `.env`

Copiez `.env.example` en `.env` et ajustez selon votre environnement.

Variables principales :

| Variable | Description | Défaut |
| --- | --- | --- |
| `GROQ_API_KEY` | Clé API Groq pour la génération de pensées | `None` |
| `FT_ENGINE_PROFIT_URL` | Endpoint profit Freqtrade | `http://ft_engine:8080/api/v1/profit` |
| `HAL_VOICE` | Voix Edge TTS utilisée | `fr-FR-HenriNeural` |
| `HAL_SPEECH_FILE` | Fichier MP3 de sortie | `speech.mp3` |
| `HAL_THOUGHT_INTERVAL` | Intervalle de boucle HAL (s) | `30` |
| `HAL_SELF_IMPROVE` | Autorise l'auto-amélioration HAL | `false` |
| `HAL_SELF_IMPROVE_EVERY` | Fréquence d'auto-amélioration | `5` |
| `HAL_CYCLE` | Cycle HAL courant | `1` |
| `LOG_LEVEL` | Niveau de logs | `INFO` |
| `PYTHON_EXECUTABLE` | Exécutable Python pour relances | `python3` |

## Réglages UI (persistants)

Les réglages utilisateur sont **locaux au navigateur** :

- Voix ON/OFF
- Son de notification ON/OFF
- Vitesse de parole
- Vitesse d'affichage texte

Ils sont stockés dans `localStorage` pour rester persistants même après redémarrage.

## Exécution locale

```bash
python -m propan run hal-brain
```

UI disponible sur `http://localhost:9000`.

## Exécution Docker

```bash
docker compose up --build
```

Le service `propan` expose l'interface sur `http://localhost:9000`.
