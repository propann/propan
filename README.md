# propan

Prototype minimal d'auto-amélioration d'une fonction Python via un modèle Groq.

## Prérequis

- Python 3.10+.
- Dépendance `groq` installée (`pip install groq`).
- Variable d'environnement `GROQ_API_KEY` définie.

## Utilisation

```bash
export GROQ_API_KEY="votre_cle_api"
python3 ouroboros.py
```

Le script lit son propre fichier, extrait la fonction `noyau_vital`, demande au modèle
une version améliorée, valide le résultat, écrit une sauvegarde (`ouroboros.py.bak`),
remplace le code et relance automatiquement le script.
