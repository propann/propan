# Interface HAL — Guide utilisateur

## Objectif

L'interface HAL est une **unique fenêtre immersive** inspirée du Nostromo (Alien) et de HAL 9000 (2001). Elle regroupe tous les états et réglages dans une page unique, sans framework UI lourd.

## Navigation

Onglets disponibles sur `/` :

- **STATUT** : pensée active, animation de réflexion, état des services (profit, Groq, voix).
- **PENSÉES** : historique horodaté des pensées HAL.
- **DONNÉES** : snapshot brut des données profit + contexte IA.
- **AUDIO** : disponibilité du MP3, lecture et messages associés.
- **RÉGLAGES** : voix ON/OFF, son notification, vitesse de parole, vitesse d'affichage texte (persistants).
- **JOURNAL** : incidents et messages système (erreurs explicites, diagnostics).

## Synchronisation texte / voix

Lorsqu'une nouvelle pensée arrive :

1. L'UI affiche une animation de réflexion.
2. L'audio est lancé si la voix est activée.
3. Le texte s'affiche **progressivement**, segment par segment, synchronisé à la durée audio.
4. Si l'audio est indisponible ou désactivé, l'affichage se cale sur la vitesse texte configurée.

## Réglages utilisateur

Les réglages sont stockés dans le navigateur (localStorage) :

- **Voix HAL active** : active/désactive toute sortie sonore.
- **Son de notification** : bip court à l'arrivée d'une pensée (silence total si voix OFF).
- **Vitesse de parole** : vitesse de lecture audio (playback rate).
- **Vitesse affichage texte** : cadence d'affichage sans audio.

## Messages d'état clairs

L'UI affiche des messages explicites si :

- le moteur profit est indisponible,
- la clé Groq est absente ou invalide,
- l'audio n'est pas généré.

L'objectif est d'offrir une lecture immédiate de l'état système sans ambiguïté.
