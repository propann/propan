import ast
import os
import groq


def noyau_vital():
    valeur = 21
    resultat = valeur * 2
    print(f"Noyau vital actif: {resultat}")
    return resultat


class MoteurEvolution:
    def __init__(self) -> None:
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY manquant dans l'environnement.")
        self.client = groq.Groq(api_key=self.api_key)

    def _lire_source(self) -> str:
        with open(__file__, "r", encoding="utf-8") as handle:
            return handle.read()

    def _extraire_noyau(self, source: str) -> str:
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "noyau_vital":
                segment = ast.get_source_segment(source, node)
                if segment:
                    return segment
        raise RuntimeError("Impossible de trouver noyau_vital dans le source.")

    def _appeler_modele(self, code_noyau: str) -> str:
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
        try:
            parsed = ast.parse(code)
        except SyntaxError as exc:
            raise RuntimeError(f"Code généré invalide: {exc}") from exc
        if not parsed.body or not isinstance(parsed.body[0], ast.FunctionDef):
            raise RuntimeError("Le code généré ne contient pas une fonction valide.")

    def _sauvegarder_backup(self, source: str) -> None:
        with open(f"{__file__}.bak", "w", encoding="utf-8") as handle:
            handle.write(source)

    def _remplacer_noyau(self, source: str, nouveau_code: str) -> str:
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
        with open(__file__, "w", encoding="utf-8") as handle:
            handle.write(source)

    def evoluer(self) -> bool:
        source = self._lire_source()
        noyau = self._extraire_noyau(source)
        nouveau_noyau = self._appeler_modele(noyau)
        self._valider_fonction(nouveau_noyau)
        self._sauvegarder_backup(source)
        nouveau_source = self._remplacer_noyau(source, nouveau_noyau)
        self._ecrire_source(nouveau_source)
        return True


if __name__ == "__main__":
    moteur = MoteurEvolution()
    if moteur.evoluer():
        os.system(f"python3 {__file__}")
