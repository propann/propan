"""Boucle d'auto-amélioration contrôlée avec interface TUI."""

from __future__ import annotations

import ast
import json
import logging
import os
import sys
import traceback
from pathlib import Path

import groq
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax

from .settings import get_settings

console = Console()
logger = logging.getLogger(__name__)


def verifier_syntaxe(code_source: str) -> bool:
    """Retourne True si le code fourni est syntaxiquement valide."""
    try:
        ast.parse(code_source)
    except SyntaxError as exc:
        logger.error("Erreur de syntaxe détectée: %s", exc)
        console.print(f"[bold red]Erreur de syntaxe détectée:[/] {exc}")
        return False
    return True


def mission_hal() -> str:
    """Mission principale de HAL à faire évoluer."""
    objectifs = [
        "Surveiller la mission",
        "Optimiser les ressources",
        "Adapter les protocoles",
    ]
    message = "HAL active ses routines: " + ", ".join(objectifs)
    return message


def afficher_interface(message_ia: str, code_source: str, cycle: int) -> None:
    """Affiche l'interface principale de HAL."""
    console.clear()
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    titre = Panel(
        f"[bold red]HAL 9000 - SYSTEME EVOLUTIF[/]  [dim]Cycle {cycle}[/]",
        border_style="red",
    )
    layout["header"].update(titre)

    logique_panel = Panel(
        message_ia,
        title="LOGIQUE NEURONALE",
        border_style="bright_red",
    )
    layout["left"].update(logique_panel)

    syntaxe = Syntax(code_source, "python", line_numbers=True)
    adn_panel = Panel(syntaxe, title="ADN SOURCE", border_style="red")
    layout["right"].update(adn_panel)

    console.print(layout)


class MemoireSysteme:
    """Gère la mémoire persistante de HAL via un fichier JSON."""

    def __init__(self, chemin: str = "hal_memoire.json") -> None:
        self.chemin = Path(__file__).with_name(chemin)
        self.donnees = {
            "generation": 0,
            "competences": [],
            "historique_ordres": [],
        }

    def charger(self) -> dict:
        """Charge la mémoire depuis le disque ou initialise les valeurs par défaut."""
        if self.chemin.exists():
            contenu = json.loads(self.chemin.read_text(encoding="utf-8"))
            if isinstance(contenu, dict):
                self.donnees["generation"] = contenu.get("generation", 0)
                self.donnees["competences"] = contenu.get("competences", [])
                self.donnees["historique_ordres"] = contenu.get("historique_ordres", [])
        return self.donnees

    def sauvegarder(self) -> None:
        """Sauvegarde la mémoire actuelle sur disque."""
        self.chemin.write_text(
            json.dumps(self.donnees, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def ajouter_competence(self, nom: str) -> None:
        """Ajoute une compétence si elle n'existe pas déjà."""
        if nom and nom not in self.donnees["competences"]:
            self.donnees["competences"].append(nom)


class MoteurEvolution:
    """Orchestre l'évolution automatique de la mission HAL."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.groq_api_key
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY manquant dans l'environnement.")
        self.client = groq.Groq(api_key=self.api_key)

    def _lire_source(self) -> str:
        """Lit le code source actuel du script."""
        return Path(__file__).read_text(encoding="utf-8")

    def _extraire_mission(self, source: str) -> str:
        """Extrait la définition de la fonction mission_hal dans le code source."""
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
                segment = ast.get_source_segment(source, node)
                if segment:
                    return segment
        raise RuntimeError("Impossible de trouver mission_hal dans le source.")

    def _appeler_modele(
        self, code_mission: str, user_input: str, competences_actuelles: str
    ) -> str:
        """Demande au modèle de proposer une version améliorée de la mission."""
        response = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es HAL. Voici tes compétences actuelles : "
                        f"{competences_actuelles}. L'utilisateur demande : "
                        f"'{user_input}'. MISSION : Réécris la fonction mission_hal. "
                        "RÈGLE ABSOLUE : Tu dois intégrer la nouvelle demande SANS "
                        "supprimer tes anciennes compétences. Si tu savais faire des maths, "
                        "continue à en faire. Si tu as importé time ou random, garde-les."
                    ),
                },
                {"role": "user", "content": code_mission},
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
        """Teste le code généré en exécutant la mission dans un scope isolé."""
        console.print("[dim]Test de la mutation en sandbox...[/]")
        try:
            ast.parse(code)
            sandbox_globals = globals().copy()
            local_scope: dict[str, object] = {}
            exec(code, sandbox_globals, local_scope)
            fonction = local_scope.get("mission_hal") or sandbox_globals.get(
                "mission_hal"
            )
            if not callable(fonction):
                console.print(
                    "[bold red]La fonction mission_hal est absente ou invalide.[/]"
                )
                return False
            resultat = fonction()
            logger.info("Résultat du test sandbox: %s", resultat)
        except Exception:
            console.print(
                "[bold red]Erreur critique lors du test sandbox (voir logs).[/]"
            )
            traceback.print_exc()
            return False
        return True

    def _detecter_nouvelles_competences(self, code: str) -> set[str]:
        """Analyse le code généré pour détecter de nouvelles bibliothèques utilisées."""
        try:
            parsed = ast.parse(code)
        except SyntaxError:
            return set()
        competences = set()
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    competences.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                competences.add(node.module.split(".")[0])
        return competences

    def _sauvegarder_backup(self, source: str) -> None:
        """Enregistre une sauvegarde du code source original."""
        Path(f"{__file__}.bak").write_text(source, encoding="utf-8")

    def _remplacer_mission(self, source: str, nouveau_code: str) -> str:
        """Remplace la fonction mission par la version générée."""
        tree = ast.parse(source)
        debut = None
        fin = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
                debut = node.lineno
                fin = node.end_lineno
                break
        if debut is None or fin is None:
            raise RuntimeError("mission_hal introuvable pour remplacement.")
        lignes = source.splitlines()
        remplacement = nouveau_code.splitlines()
        nouveau_source = lignes[: debut - 1] + remplacement + lignes[fin:]
        return "\n".join(nouveau_source) + "\n"

    def _ecrire_source(self, source: str) -> None:
        """Écrit le code source mis à jour dans le fichier actuel."""
        Path(__file__).write_text(source, encoding="utf-8")

    def evoluer(self, cycle: int) -> bool:
        """Lance un cycle complet d'évolution et relance le script si succès."""
        memoire = MemoireSysteme()
        donnees_memoire = memoire.charger()
        competences = donnees_memoire.get("competences", [])
        competences_actuelles = ", ".join(competences) if competences else "aucune"
        source = self._lire_source()
        mission = self._extraire_mission(source)
        message_ia = mission_hal()
        afficher_interface(message_ia, mission, cycle)
        user_input = console.input(
            "[bold red]Dave, une instruction pour ma prochaine mutation ? > [/]"
        )
        nouveau_mission = self._appeler_modele(
            mission, user_input, competences_actuelles
        )
        self._valider_fonction(nouveau_mission)
        if self._tester_sandbox(nouveau_mission):
            nouveau_source = self._remplacer_mission(source, nouveau_mission)
        else:
            console.print(
                "[bold red]MUTATION REJETÉE : Erreur détectée en sandbox.[/]"
            )
            return False
        if verifier_syntaxe(nouveau_source):
            donnees_memoire["generation"] = cycle
            donnees_memoire["historique_ordres"].append(user_input)
            nouvelles_competences = self._detecter_nouvelles_competences(
                nouveau_mission
            )
            for competence in nouvelles_competences:
                memoire.ajouter_competence(competence)
            memoire.sauvegarder()
            self._sauvegarder_backup(source)
            self._ecrire_source(nouveau_source)
            os.environ["HAL_CYCLE"] = str(cycle + 1)
            os.execv(sys.executable, [sys.executable, __file__])
        console.print("[bold red]MUTATION REJETÉE : Le code reçu est corrompu.[/]")
        return False


def main() -> None:
    """Point d'entrée principal pour HAL."""
    settings = get_settings()
    moteur = MoteurEvolution()
    moteur.evoluer(settings.hal_cycle)


if __name__ == "__main__":
    main()
