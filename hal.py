"""Boucle d'auto-amélioration contrôlée avec interface TUI."""

import ast  # Analyse syntaxique pour valider et manipuler le code.
import json  # Gestion de la mémoire persistante.
import os  # Accès à l'environnement et relance du script.

import groq  # Client d'accès au modèle Groq.
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def verifier_syntaxe(code_source: str) -> bool:
    """Retourne True si le code fourni est syntaxiquement valide."""
    try:
        ast.parse(code_source)  # Vérifie la syntaxe du code reçu.
    except SyntaxError as exc:
        console.print(f"[bold red]Erreur de syntaxe détectée:[/] {exc}")
        return False  # Signale un échec de validation.
    return True  # La syntaxe est correcte.


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
        self.chemin = os.path.join(os.path.dirname(__file__), chemin)
        self.donnees = {
            "generation": 0,
            "competences": [],
            "historique_ordres": [],
        }

    def charger(self) -> dict:
        """Charge la mémoire depuis le disque ou initialise les valeurs par défaut."""
        if os.path.exists(self.chemin):
            with open(self.chemin, "r", encoding="utf-8") as handle:
                contenu = json.load(handle)
            if isinstance(contenu, dict):
                self.donnees["generation"] = contenu.get("generation", 0)
                self.donnees["competences"] = contenu.get("competences", [])
                self.donnees["historique_ordres"] = contenu.get(
                    "historique_ordres", []
                )
        return self.donnees

    def sauvegarder(self) -> None:
        """Sauvegarde la mémoire actuelle sur disque."""
        with open(self.chemin, "w", encoding="utf-8") as handle:
            json.dump(self.donnees, handle, ensure_ascii=False, indent=2)

    def ajouter_competence(self, nom: str) -> None:
        """Ajoute une compétence si elle n'existe pas déjà."""
        if nom and nom not in self.donnees["competences"]:
            self.donnees["competences"].append(nom)


class MoteurEvolution:
    """Orchestre l'évolution automatique de la mission HAL."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("GROQ_API_KEY")  # Récupère la clé API.
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY manquant dans l'environnement.")
        self.client = groq.Groq(api_key=self.api_key)  # Initialise le client Groq.

    def _lire_source(self) -> str:
        """Lit le code source actuel du script."""
        with open(__file__, "r", encoding="utf-8") as handle:
            return handle.read()  # Retourne tout le fichier source.

    def _extraire_mission(self, source: str) -> str:
        """Extrait la définition de la fonction mission_hal dans le code source."""
        tree = ast.parse(source)  # Parse l'AST du code source.
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
                segment = ast.get_source_segment(source, node)  # Extrait la source.
                if segment:
                    return segment  # Retourne le code de la fonction.
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
        contenu = response.choices[0].message.content  # Récupère le contenu généré.
        if not contenu:
            raise RuntimeError("Réponse vide du modèle.")
        return contenu.strip()  # Nettoie et renvoie le code.

    def _valider_fonction(self, code: str) -> None:
        """Valide que le code reçu contient une fonction Python correcte."""
        try:
            parsed = ast.parse(code)  # Parse le code pour détecter les erreurs.
        except SyntaxError as exc:
            raise RuntimeError(f"Code généré invalide: {exc}") from exc
        if not parsed.body or not isinstance(parsed.body[0], ast.FunctionDef):
            raise RuntimeError("Le code généré ne contient pas une fonction valide.")

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
        with open(f"{__file__}.bak", "w", encoding="utf-8") as handle:
            handle.write(source)  # Écrit le backup sur disque.

    def _remplacer_mission(self, source: str, nouveau_code: str) -> str:
        """Remplace la fonction mission par la version générée."""
        tree = ast.parse(source)  # Parse pour localiser la fonction.
        debut = None  # Ligne de début de la fonction mission.
        fin = None  # Ligne de fin de la fonction mission.
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
                debut = node.lineno  # Capture la ligne de début.
                fin = node.end_lineno  # Capture la ligne de fin.
                break
        if debut is None or fin is None:
            raise RuntimeError("mission_hal introuvable pour remplacement.")
        lignes = source.splitlines()  # Découpe le source en lignes.
        remplacement = nouveau_code.splitlines()  # Découpe le nouveau code.
        nouveau_source = lignes[: debut - 1] + remplacement + lignes[fin:]
        return "\n".join(nouveau_source) + "\n"  # Reconstruit le fichier.

    def _ecrire_source(self, source: str) -> None:
        """Écrit le code source mis à jour dans le fichier actuel."""
        with open(__file__, "w", encoding="utf-8") as handle:
            handle.write(source)  # Sauvegarde le nouveau source.

    def evoluer(self, cycle: int) -> bool:
        """Lance un cycle complet d'évolution et relance le script si succès."""
        memoire = MemoireSysteme()
        donnees_memoire = memoire.charger()
        competences = donnees_memoire.get("competences", [])
        competences_actuelles = ", ".join(competences) if competences else "aucune"
        source = self._lire_source()  # Charge le code actuel.
        mission = self._extraire_mission(source)  # Extrait la mission.
        message_ia = mission_hal()  # Exécute la mission actuelle.
        afficher_interface(message_ia, mission, cycle)
        user_input = console.input(
            "[bold red]Dave, une instruction pour ma prochaine mutation ? > [/]"
        )
        nouveau_mission = self._appeler_modele(
            mission, user_input, competences_actuelles
        )  # Génère.
        self._valider_fonction(nouveau_mission)  # Valide la sortie.
        nouveau_source = self._remplacer_mission(source, nouveau_mission)  # Remplace.
        if verifier_syntaxe(nouveau_source):
            donnees_memoire["generation"] = cycle
            donnees_memoire["historique_ordres"].append(user_input)
            nouvelles_competences = self._detecter_nouvelles_competences(
                nouveau_mission
            )
            for competence in nouvelles_competences:
                memoire.ajouter_competence(competence)
            memoire.sauvegarder()
            self._sauvegarder_backup(source)  # Sauvegarde l'ancien code.
            self._ecrire_source(nouveau_source)  # Écrit le nouveau code.
            os.environ["HAL_CYCLE"] = str(cycle + 1)
            os.execv(
                os.getenv("PYTHON_EXECUTABLE", "python3"),
                ["python3", __file__],
            )
        console.print("[bold red]MUTATION REJETÉE : Le code reçu est corrompu.[/]")
        return False  # Indique que l'évolution a échoué.


if __name__ == "__main__":
    moteur = MoteurEvolution()  # Initialise le moteur.
    cycle_actuel = int(os.environ.get("HAL_CYCLE", "1"))
    moteur.evoluer(cycle_actuel)  # Démarre l'évolution.
