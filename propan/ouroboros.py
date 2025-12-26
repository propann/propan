"""Boucle d'auto-amélioration contrôlée autour d'une fonction noyau."""

from __future__ import annotations

import ast
import logging
import os
import sys
import traceback
from pathlib import Path

import groq

from .settings import get_settings

logger = logging.getLogger(__name__)


def verifier_syntaxe(code_source: str) -> bool:
    """Retourne True si le code fourni est syntaxiquement valide."""
    try:
        ast.parse(code_source)
    except SyntaxError as exc:
        logger.error("Erreur de syntaxe détectée: %s", exc)
        return False
    return True


def noyau_vital() -> int:
    """Fonction noyau que l'agent va tenter d'améliorer."""
    valeur = 21
    resultat = valeur * 2
    logger.info("Noyau vital actif: %s", resultat)
    return resultat


class MoteurEvolution:
    """Orchestre l'évolution automatique du noyau vital."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.groq_api_key
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY manquant dans l'environnement.")
        self.client = groq.Groq(api_key=self.api_key)

    def _lire_source(self) -> str:
        """Lit le code source actuel du script."""
        return Path(__file__).read_text(encoding="utf-8")

    def _extraire_noyau(self, source: str) -> str:
        """Extrait la définition de la fonction noyau dans le code source."""
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "noyau_vital":
                segment = ast.get_source_segment(source, node)
                if segment:
                    return segment
        raise RuntimeError("Impossible de trouver noyau_vital dans le source.")

    def _appeler_modele(self, code_noyau: str) -> str:
        """Demande au modèle de proposer une version améliorée du noyau."""
        response = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un moteur d'évolution. Réécris cette fonction Python pour la "
                        "rendre plus complexe, optimisée ou créative. Renvoie UNIQUEMENT le "
                        "code Python valide."
                    ),
                },
                {"role": "user", "content": code_noyau},
            ],
        )
        contenu = response.choices[0].message.content
        if not contenu:
            raise RuntimeError("Réponse vide du modèle.")
        return contenu.strip()

    def _valider_fonction(self, code: str) -> None:
        """Valide que le code reçu contient une fonction Python correcte."""
        try:
            parsed = ast.parse(code)
        except SyntaxError as exc:
            raise RuntimeError(f"Code généré invalide: {exc}") from exc
        if not parsed.body or not isinstance(parsed.body[0], ast.FunctionDef):
            raise RuntimeError("Le code généré ne contient pas une fonction valide.")

    def _tester_sandbox(self, code: str) -> bool:
        """Teste le code généré en exécutant la fonction dans un scope isolé."""
        logger.info("Test de la mutation en sandbox.")
        try:
            ast.parse(code)
            sandbox_globals = globals().copy()
            local_scope: dict[str, object] = {}
            exec(code, sandbox_globals, local_scope)
            fonction = local_scope.get("noyau_vital") or sandbox_globals.get("noyau_vital")
            if not callable(fonction):
                logger.error("La fonction noyau_vital est absente ou invalide.")
                return False
            resultat = fonction()
            logger.info("Résultat du test sandbox: %s", resultat)
        except (SyntaxError, ValueError, TypeError, RuntimeError, NameError) as exc:
            logger.error("Erreur critique lors du test sandbox: %s", exc)
            traceback.print_exc()
            return False
        return True

    def _sauvegarder_backup(self, source: str) -> None:
        """Enregistre une sauvegarde du code source original."""
        Path(f"{__file__}.bak").write_text(source, encoding="utf-8")

    def _remplacer_noyau(self, source: str, nouveau_code: str) -> str:
        """Remplace la fonction noyau par la version générée."""
        tree = ast.parse(source)
        debut = None
        fin = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "noyau_vital":
                debut = node.lineno
                fin = node.end_lineno
                break
        if debut is None or fin is None:
            raise RuntimeError("noyau_vital introuvable pour remplacement.")
        lignes = source.splitlines()
        remplacement = nouveau_code.splitlines()
        nouveau_source = lignes[: debut - 1] + remplacement + lignes[fin:]
        return "\n".join(nouveau_source) + "\n"

    def _ecrire_source(self, source: str) -> None:
        """Écrit le code source mis à jour dans le fichier actuel."""
        Path(__file__).write_text(source, encoding="utf-8")

    def evoluer(self) -> bool:
        """Lance un cycle complet d'évolution et relance le script si succès."""
        source = self._lire_source()
        noyau = self._extraire_noyau(source)
        nouveau_noyau = self._appeler_modele(noyau)
        self._valider_fonction(nouveau_noyau)
        if self._tester_sandbox(nouveau_noyau):
            nouveau_source = self._remplacer_noyau(source, nouveau_noyau)
        else:
            logger.error("MUTATION REJETÉE : Erreur détectée en sandbox.")
            return False
        if verifier_syntaxe(nouveau_source):
            self._sauvegarder_backup(source)
            self._ecrire_source(nouveau_source)
            os.execv(sys.executable, [sys.executable, __file__])
        logger.error("MUTATION REJETÉE : Le code reçu est corrompu.")
        return False


def main() -> None:
    """Point d'entrée principal pour Ouroboros."""
    moteur = MoteurEvolution()
    moteur.evoluer()


if __name__ == "__main__":
    main()
