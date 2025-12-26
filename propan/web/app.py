"""Flask application factory for the HAL brain web UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from flask import Flask

from ..services import CommentaryService, ProfitService, ThoughtStore, TTSService
from ..settings import get_settings
from .routes_api import api_bp
from .routes_ui import ui_bp


@dataclass
class AppState:
    """Holds shared state for the HAL brain web app."""

    settings: object
    profit_service: ProfitService
    commentary_service: CommentaryService
    tts_service: TTSService
    thought_store: ThoughtStore
    last_profit: dict = field(default_factory=dict)
    last_profit_status: str = "unknown"
    last_profit_error: str | None = None
    last_profit_at: str | None = None
    last_commentary: str = "HAL is booting."
    last_commentary_status: str = "unknown"
    last_commentary_error: str | None = None
    last_commentary_at: str | None = None
    last_audio_status: str = "unknown"
    last_audio_error: str | None = None
    last_audio_at: str | None = None

    def touch_profit(self, status: str, data: dict, error: str | None) -> None:
        self.last_profit_status = status
        self.last_profit = data
        self.last_profit_error = error
        self.last_profit_at = _now_iso()

    def touch_commentary(self, status: str, text: str, error: str | None) -> None:
        self.last_commentary_status = status
        self.last_commentary = text
        self.last_commentary_error = error
        self.last_commentary_at = _now_iso()

    def touch_audio(self, status: str, error: str | None) -> None:
        self.last_audio_status = status
        self.last_audio_error = error
        self.last_audio_at = _now_iso()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    settings = get_settings()

    state = AppState(
        settings=settings,
        profit_service=ProfitService(settings),
        commentary_service=CommentaryService(settings),
        tts_service=TTSService(settings),
        thought_store=ThoughtStore(),
    )
    state.thought_store.add(state.last_commentary, source="system")
    if not settings.ft_engine_profit_url:
        state.touch_profit(
            status="disabled",
            data={},
            error="FT_ENGINE_PROFIT_URL is empty; profit fetching disabled.",
        )
    if not settings.groq_api_key:
        state.touch_commentary(
            status="disabled",
            text=state.last_commentary,
            error="GROQ_API_KEY missing.",
        )

    app.extensions["state"] = state
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)

    return app
