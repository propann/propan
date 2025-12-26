# Architecture Propan

## Vue d'ensemble

Le service **HAL Brain** expose une UI web unique (onglets) et un ensemble d'endpoints API stables. Une boucle de fond rafraîchit périodiquement les profits, la pensée HAL et la synthèse vocale. Les erreurs (Groq, moteur profit, audio) sont centralisées pour affichage dans l'UI et le diagnostic.

## Flux principal

1. **Boucle HAL** (`propan/hal_brain.py`)
   - Récupère les profits via `ProfitService`.
   - Génère une pensée via `CommentaryService`.
   - Stocke les pensées dans `ThoughtStore`.
   - Produit un MP3 via `TTSService`.

2. **UI web** (`propan/web/routes_ui.py`)
   - Page unique avec onglets (Overview, Profit, Thoughts, Logs, Audio, Settings).
   - Rafraîchissement périodique par appels API.

3. **API** (`propan/web/routes_api.py`)
   - `/api/health` : état consolidé.
   - `/api/profit` : snapshot profit.
   - `/api/thoughts` + `/api/thoughts/clear`.
   - `/api/audio` : disponibilité audio.

## Modules clés

- `propan/web/app.py`
  - Factory Flask, création de l'état partagé `AppState`.
- `propan/services/profit.py`
  - Récupération profit + messages d'erreurs explicites (host `ft_engine` etc.).
- `propan/services/commentary.py`
  - Génération Groq, erreurs 401 explicites.
- `propan/services/tts.py`
  - Génération MP3 via Edge TTS.
- `propan/services/thought_store.py`
  - Stockage en mémoire des pensées.

## Diagramme simplifié

```
[Browser UI] -> /api/* ----> [Flask App + AppState]
                             |-> ProfitService -> FT engine
                             |-> CommentaryService -> Groq API
                             |-> TTSService -> speech.mp3
                             |-> ThoughtStore (in-memory)
```

## Notes d'exécution

- La boucle HAL tourne dans un thread séparé (intervalle `HAL_THOUGHT_INTERVAL`).
- L'UI ne déclenche pas de requête audio si le MP3 est absent.
- `/speech.mp3` et `/favicon.ico` renvoient 204 si non disponibles pour éviter les 404.
