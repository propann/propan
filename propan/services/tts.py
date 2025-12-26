"""Text-to-speech service wrapper."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import edge_tts

from ..settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    """Outcome of a speech generation."""

    status: str
    path: Path | None = None
    error: str | None = None


class TTSService:
    """Generate a speech file using Edge TTS."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, text: str) -> TTSResult:
        """Generate speech audio for text."""
        if not text:
            return TTSResult(status="skipped", error="Texte vide")

        async def _run() -> None:
            communicate = edge_tts.Communicate(text=text, voice=self._settings.hal_voice)
            await communicate.save(str(self._settings.hal_speech_file))

        try:
            asyncio.run(_run())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_run())
            loop.close()
        except Exception as exc:  # noqa: BLE001
            logger.error("Speech generation failed: %s", exc)
            return TTSResult(status="error", error=f"Erreur synthèse vocale : {exc}")

        return TTSResult(status="ok", path=self._settings.hal_speech_file)
