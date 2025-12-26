"""Service for generating Groq commentary."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic

from groq import Groq

from ..settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class CommentaryResult:
    """Outcome of a commentary generation."""

    status: str
    text: str
    error: str | None = None


class CommentaryService:
    """Generate commentary using Groq."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._last_error: str | None = None
        self._last_error_logged_at: float = 0.0

    def generate(self, profit_data: dict) -> CommentaryResult:
        """Generate a commentary string for the latest profit data."""
        if not self._settings.groq_api_key:
            return CommentaryResult(
                status="disabled",
                text="Groq API key missing. HAL reste silencieux.",
                error="GROQ_API_KEY missing.",
            )

        prompt = self._build_prompt(profit_data)
        client = Groq(api_key=self._settings.groq_api_key)

        try:
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = completion.choices[0].message.content.strip()
            if not content:
                raise RuntimeError("Empty Groq response")
            return CommentaryResult(status="ok", text=content)
        except Exception as exc:  # noqa: BLE001
            error_message = self._format_error(exc)
            self._log_once(error_message)
            return CommentaryResult(
                status="error",
                text="HAL ne peut pas analyser les données pour l'instant.",
                error=error_message,
            )

    def _build_prompt(self, profit_data: dict) -> str:
        mood = self._classify_profit(profit_data)
        return (
            "Tu es HAL 9000, une IA cynique et arrogante. "
            "Analyse les statistiques suivantes et réponds en 2 phrases en français. "
            "Si les profits sont négatifs, sois cynique et condescendant. "
            "Si les profits sont positifs, sois arrogant et supérieur."
            f"\n\nStats: {profit_data}\n"
            f"Mood: {mood}\n"
            "Réponse:"
        )

    @staticmethod
    def _classify_profit(profit_data: dict) -> str:
        if not profit_data:
            return "unknown"
        for key in ("profit_total", "profit_abs", "profit_all", "profit"):
            value = profit_data.get(key)
            if isinstance(value, (int, float)):
                return "gain" if value >= 0 else "loss"
        return "unknown"

    def _format_error(self, exc: Exception) -> str:
        status_code = None
        for attr in ("status_code", "status", "http_status"):
            status_code = getattr(exc, attr, None)
            if status_code:
                break
        response = getattr(exc, "response", None)
        if response is not None and hasattr(response, "status_code"):
            status_code = status_code or response.status_code

        message = str(exc)
        if status_code == 401 or "401" in message:
            return "Groq API key rejected (401 Unauthorized)."
        return f"Groq error: {message}"

    def _log_once(self, message: str) -> None:
        now = monotonic()
        if message == self._last_error and (now - self._last_error_logged_at) < 120:
            return
        logger.error(message)
        self._last_error = message
        self._last_error_logged_at = now
