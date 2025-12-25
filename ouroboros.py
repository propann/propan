"""Boucle d'auto-amélioration contrôlée autour d'une fonction noyau."""

import ast  # Analyse syntaxique pour valider et manipuler le code.
import os  # Accès à l'environnement et relance du script.
import groq  # Client d'accès au modèle Groq.


def verifier_syntaxe(code_source: str) -> bool:
    """Retourne True si le code fourni est syntaxiquement valide."""
    try:
        ast.parse(code_source)  # Vérifie la syntaxe du code reçu.
    except SyntaxError as exc:
        print(f"Erreur de syntaxe détectée: {exc}")  # Informe l'utilisateur.
        return False  # Signale un échec de validation.
    return True  # La syntaxe est correcte.


def noyau_vital():
    """Fonction noyau que l'agent va tenter d'améliorer."""
    valeur = 21  # Valeur de base pour le calcul.
    resultat = valeur * 2  # Calcul simple pour démonstration.
    print(f"Noyau vital actif: {resultat}")  # Trace l'activité du noyau.
    return resultat  # Retourne le résultat final.


class MoteurEvolution:
    """Orchestre l'évolution automatique du noyau vital."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("GROQ_API_KEY")  # Récupère la clé API.
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY manquant dans l'environnement.")
        self.client = groq.Groq(api_key=self.api_key)  # Initialise le client Groq.

    def _lire_source(self) -> str:
        """Lit le code source actuel du script."""
        with open(__file__, "r", encoding="utf-8") as handle:
            return handle.read()  # Retourne tout le fichier source.

    def _extraire_noyau(self, source: str) -> str:
        """Extrait la définition de la fonction noyau dans le code source."""
        tree = ast.parse(source)  # Parse l'AST du code source.
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "noyau_vital":
                segment = ast.get_source_segment(source, node)  # Extrait la source.
                if segment:
                    return segment  # Retourne le code de la fonction.
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

    def _sauvegarder_backup(self, source: str) -> None:
        """Enregistre une sauvegarde du code source original."""
        with open(f"{__file__}.bak", "w", encoding="utf-8") as handle:
            handle.write(source)  # Écrit le backup sur disque.

    def _remplacer_noyau(self, source: str, nouveau_code: str) -> str:
        """Remplace la fonction noyau par la version générée."""
        tree = ast.parse(source)  # Parse pour localiser la fonction.
        debut = None  # Ligne de début de la fonction noyau.
        fin = None  # Ligne de fin de la fonction noyau.
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "noyau_vital":
                debut = node.lineno  # Capture la ligne de début.
                fin = node.end_lineno  # Capture la ligne de fin.
                break
        if debut is None or fin is None:
            raise RuntimeError("noyau_vital introuvable pour remplacement.")
        lignes = source.splitlines()  # Découpe le source en lignes.
        remplacement = nouveau_code.splitlines()  # Découpe le nouveau code.
        nouveau_source = lignes[: debut - 1] + remplacement + lignes[fin:]
        return "\n".join(nouveau_source) + "\n"  # Reconstruit le fichier.

    def _ecrire_source(self, source: str) -> None:
        """Écrit le code source mis à jour dans le fichier actuel."""
        with open(__file__, "w", encoding="utf-8") as handle:
            handle.write(source)  # Sauvegarde le nouveau source.

    def evoluer(self) -> bool:
        """Lance un cycle complet d'évolution et relance le script si succès."""
        source = self._lire_source()  # Charge le code actuel.
        noyau = self._extraire_noyau(source)  # Extrait le noyau.
        nouveau_noyau = self._appeler_modele(noyau)  # Génère une nouvelle version.
        self._valider_fonction(nouveau_noyau)  # Valide la sortie.
        nouveau_source = self._remplacer_noyau(source, nouveau_noyau)  # Remplace.
        if verifier_syntaxe(nouveau_source):
            self._sauvegarder_backup(source)  # Sauvegarde l'ancien code.
            self._ecrire_source(nouveau_source)  # Écrit le nouveau code.
            os.execv(  # Relance immédiatement le script avec le nouveau code.
                os.getenv("PYTHON_EXECUTABLE", "python3"),
                ["python3", __file__],
            )
        print("\033[91mMUTATION REJETÉE : Le code reçu est corrompu.\033[0m")
        return False  # Indique que l'évolution a échoué.


if __name__ == "__main__":
    moteur = MoteurEvolution()  # Initialise le moteur.
    moteur.evoluer()  # Démarre l'évolution.
