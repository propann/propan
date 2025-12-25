"""Tableau de bord HAL 9000 avec mutation automatique via Groq."""

import ast
import os
import time
from typing import Optional

import groq
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def mission_hal() -> str:
    """Mission principale de HAL : renvoie un message de statut."""
    systemes = [
        "Analyse des signaux",
        "Surveillance orbitale",
        "Synchronisation cognitive",
    ]
    return "HAL opère ses protocoles: " + ", ".join(systemes)


def generate_dashboard() -> Layout:
    """Construit le layout principal du tableau de bord."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=2),
    )
    return layout


def _panel_header() -> Panel:
    """Retourne le panneau du header."""
    return Panel(
        "HAL 9000 // SYSTEM MONITOR",
        style="white on red",
        padding=(0, 2),
    )


def _read_source() -> str:
    """Lit le code source actuel du script."""
    with open(__file__, "r", encoding="utf-8") as handle:
        return handle.read()


def _extract_mission(source: str) -> str:
    """Extrait la fonction mission_hal depuis le code source."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
            segment = ast.get_source_segment(source, node)
            if segment:
                return segment
    raise RuntimeError("mission_hal introuvable dans le code source.")


def _update_panels(
    layout: Layout,
    message: str,
    mission_code: str,
    status: str,
) -> None:
    """Met à jour les panneaux du dashboard."""
    layout["header"].update(_panel_header())

    interface_panel = Panel(
        message,
        title="INTERFACE VOCALE",
        border_style="bright_red",
    )
    layout["left"].update(interface_panel)

    syntax = Syntax(mission_code, "python", line_numbers=True)
    noyau_panel = Panel(
        syntax,
        title="NOYAU PYTHON",
        border_style="red",
    )
    layout["right"].update(noyau_panel)

    footer_panel = Panel(
        status,
        title="STATUT",
        border_style="red",
    )
    layout["footer"].update(footer_panel)


def _call_groq(client: groq.Groq, mission_code: str, user_input: str) -> str:
    """Appelle Groq pour générer une nouvelle version de mission_hal."""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es HAL. L'utilisateur a dit : "
                    f"'{user_input}'. Réécris la fonction Python 'mission_hal' pour retourner "
                    "une réponse adaptée (agressive, passive, ou serviable). Change "
                    "aussi un peu la logique interne."
                ),
            },
            {"role": "user", "content": mission_code},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Réponse vide du modèle.")
    return content.strip()


def _validate_mission(code: str) -> None:
    """Valide que le code représente une fonction mission_hal correcte."""
    try:
        parsed = ast.parse(code)
    except SyntaxError as exc:
        raise RuntimeError(f"Code généré invalide: {exc}") from exc
    if not parsed.body or not isinstance(parsed.body[0], ast.FunctionDef):
        raise RuntimeError("Le code généré ne contient pas une fonction valide.")
    if parsed.body[0].name != "mission_hal":
        raise RuntimeError("La fonction générée n'est pas mission_hal.")


def _replace_mission(source: str, new_code: str) -> str:
    """Remplace la fonction mission_hal dans le fichier source."""
    tree = ast.parse(source)
    start = None
    end = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "mission_hal":
            start = node.lineno
            end = node.end_lineno
            break
    if start is None or end is None:
        raise RuntimeError("mission_hal introuvable pour remplacement.")
    lines = source.splitlines()
    new_lines = new_code.splitlines()
    updated = lines[: start - 1] + new_lines + lines[end:]
    return "\n".join(updated) + "\n"


def _write_source(source: str) -> None:
    """Écrit le nouveau source dans le fichier courant."""
    with open(__file__, "w", encoding="utf-8") as handle:
        handle.write(source)


def _backup_source(source: str) -> None:
    """Sauvegarde le fichier source courant."""
    with open(f"{__file__}.bak", "w", encoding="utf-8") as handle:
        handle.write(source)


def _refresh_once(
    layout: Layout,
    message: str,
    mission_code: str,
    status: str,
) -> None:
    """Rafraîchit le dashboard une fois."""
    _update_panels(layout, message, mission_code, status)
    with Live(layout, refresh_per_second=4, console=console):
        time.sleep(0.2)


def run_dashboard() -> None:
    """Boucle principale d'affichage et mutation de HAL."""
    api_key = os.environ.get("GROQ_API_KEY")
    client: Optional[groq.Groq] = None
    if api_key:
        client = groq.Groq(api_key=api_key)

    cycle = int(os.environ.get("HAL_CYCLE", "1"))
    status = "Prêt pour le prochain cycle."

    while True:
        source = _read_source()
        mission_code = _extract_mission(source)
        message = mission_hal()

        status = "Ordre pour le prochain cycle ?"
        layout = generate_dashboard()
        _refresh_once(layout, message, mission_code, status)

        user_input = console.input("Ordre pour le prochain cycle ? ")
        status = "Mutation en cours..."
        layout = generate_dashboard()
        _refresh_once(layout, message, mission_code, status)

        if not client:
            status = "[bold red]Connexion Perdue[/]"
            layout = generate_dashboard()
            _refresh_once(layout, message, mission_code, status)
            continue

        try:
            new_mission = _call_groq(client, mission_code, user_input)
        except Exception:
            status = "[bold red]Connexion Perdue[/]"
            layout = generate_dashboard()
            _refresh_once(layout, message, mission_code, status)
            continue

        try:
            _validate_mission(new_mission)
            new_source = _replace_mission(source, new_mission)
            ast.parse(new_source)
        except Exception as exc:
            status = f"[bold red]Mutation rejetée[/]: {exc}"
            layout = generate_dashboard()
            _refresh_once(layout, message, mission_code, status)
            continue

        _backup_source(source)
        _write_source(new_source)
        os.environ["HAL_CYCLE"] = str(cycle + 1)
        os.execv(
            os.getenv("PYTHON_EXECUTABLE", "python3"),
            ["python3", __file__],
        )


if __name__ == "__main__":
    run_dashboard()
