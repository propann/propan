"""CLI for Propan."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Iterable

import typer

from .logging_utils import configure_logging
from .settings import get_settings

app = typer.Typer(help="HAL/Ouroboros command center.")
run_app = typer.Typer(help="Run core agents.")
app.add_typer(run_app, name="run")

logger = logging.getLogger(__name__)


@app.callback()
def main() -> None:
    """Initialize logging for CLI."""
    configure_logging()


@run_app.command("hal")
def run_hal() -> None:
    """Run the HAL self-evolution loop."""
    from . import hal

    try:
        hal.main()
    except Exception as exc:  # noqa: BLE001
        logger.error("HAL run failed: %s", exc)
        raise typer.Exit(code=1) from exc


@run_app.command("ouroboros")
def run_ouroboros() -> None:
    """Run the Ouroboros loop."""
    from . import ouroboros

    try:
        ouroboros.main()
    except Exception as exc:  # noqa: BLE001
        logger.error("Ouroboros run failed: %s", exc)
        raise typer.Exit(code=1) from exc


@run_app.command("hal-brain")
def run_hal_brain() -> None:
    """Run the HAL brain web service."""
    from . import hal_brain

    try:
        hal_brain.main()
    except Exception as exc:  # noqa: BLE001
        logger.error("HAL brain failed: %s", exc)
        raise typer.Exit(code=1) from exc


@app.command("dashboard")
def run_dashboard() -> None:
    """Run the HAL dashboard TUI."""
    from . import hal_dashboard

    try:
        hal_dashboard.main()
    except Exception as exc:  # noqa: BLE001
        logger.error("Dashboard failed: %s", exc)
        raise typer.Exit(code=1) from exc


def _check_dependencies(modules: Iterable[str]) -> list[str]:
    missing = []
    for module in modules:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


@app.command("doctor")
def doctor() -> None:
    """Check environment variables, dependencies, and connectivity."""
    settings = get_settings()
    issues: list[str] = []

    typer.echo("🩺 Propan doctor report")

    if not settings.groq_api_key:
        issues.append("GROQ_API_KEY manquant (nécessaire pour HAL/Ouroboros).")
    else:
        typer.echo("✔ GROQ_API_KEY détectée")

    required_modules = [
        "groq",
        "requests",
        "edge_tts",
        "flask",
        "rich",
        "typer",
        "pydantic_settings",
        "dotenv",
    ]
    missing = _check_dependencies(required_modules)
    if missing:
        issues.append(f"Dépendances manquantes: {', '.join(missing)}")
    else:
        typer.echo("✔ Dépendances Python OK")

    if settings.ft_engine_profit_url and "requests" not in missing:
        import requests

        try:
            response = requests.get(settings.ft_engine_profit_url, timeout=5)
            response.raise_for_status()
            typer.echo("✔ Accès réseau OK vers FT engine")
        except Exception as exc:  # noqa: BLE001
            issues.append(f"Accès réseau KO vers FT engine: {exc}")

    if issues:
        typer.echo("\n⚠️  Problèmes détectés:")
        for issue in issues:
            typer.echo(f"- {issue}")
        raise typer.Exit(code=1)

    typer.echo("\n✅ Tout est opérationnel.")
