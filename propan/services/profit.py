"""Service for fetching profit data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlparse

import requests

from ..settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class ProfitResult:
    """Outcome of a profit fetch."""

    status: str
    data: dict
    error: str | None = None


class ProfitService:
    """Fetch profit data from the configured engine."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._last_error: str | None = None
        self._last_error_logged_at: float = 0.0

    def fetch(self) -> ProfitResult:
        """Fetch profit data, returning a structured result."""
        url = self._settings.ft_engine_profit_url
        if not url:
            return ProfitResult(
                status="disabled",
                data={},
                error=(
                    "FT_ENGINE_PROFIT_URL est vide ; la récupération des profits est désactivée."
                ),
            )

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            error_message = self._format_error(url, exc)
            self._log_once(error_message)
            return ProfitResult(status="error", data={}, error=error_message)
        except ValueError as exc:
            error_message = f"Charge utile profit invalide : {exc}"
            self._log_once(error_message)
            return ProfitResult(status="error", data={}, error=error_message)

        if not isinstance(payload, dict):
            error_message = "La charge utile profit n'est pas un objet JSON."
            self._log_once(error_message)
            return ProfitResult(status="error", data={}, error=error_message)

        return ProfitResult(status="ok", data=payload, error=None)

    def _format_error(self, url: str, exc: Exception) -> str:
        parsed = urlparse(url)
        host = parsed.hostname or "unknown"
        message = str(exc)

        if host == "ft_engine":
            return (
                "L'hôte FT engine 'ft_engine' est injoignable depuis un lancement local. "
                "Utilisez docker compose ou définissez FT_ENGINE_PROFIT_URL sur un hôte "
                f"joignable. Erreur d'origine : {message}"
            )

        return f"Échec de récupération profit pour {url} : {message}"

    def _log_once(self, message: str) -> None:
        now = monotonic()
        if message == self._last_error and (now - self._last_error_logged_at) < 120:
            return
        logger.warning(message)
        self._last_error = message
        self._last_error_logged_at = now
