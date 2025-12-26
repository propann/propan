"""HAL brain service: web UI + background commentary loop."""

from __future__ import annotations

import logging
import threading
import time

from .web.app import AppState, create_app

logger = logging.getLogger(__name__)


def _run_web(app) -> None:
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


def _brain_loop(state: AppState) -> None:
    interval = state.settings.hal_thought_interval
    while True:
        try:
            profit_result = state.profit_service.fetch()
            state.touch_profit(
                profit_result.status, profit_result.data, profit_result.error
            )

            commentary_result = state.commentary_service.generate(profit_result.data)
            state.touch_commentary(
                commentary_result.status,
                commentary_result.text,
                commentary_result.error,
            )
            state.thought_store.add(
                commentary_result.text,
                source="groq" if commentary_result.status == "ok" else "system",
            )

            if commentary_result.status == "ok":
                tts_result = state.tts_service.generate(commentary_result.text)
                state.touch_audio(tts_result.status, tts_result.error)
            else:
                state.touch_audio(
                    status=(
                        "disabled"
                        if commentary_result.status == "disabled"
                        else "skipped"
                    ),
                    error=None,
                )

            logger.info("HAL thought: %s", commentary_result.text)
        except Exception as exc:  # noqa: BLE001
            logger.error("HAL brain loop failed: %s", exc)
        time.sleep(interval)


def main() -> None:
    """Start HAL brain web + loop."""
    app = create_app()
    state: AppState = app.extensions["state"]

    web_thread = threading.Thread(target=_run_web, args=(app,), daemon=True)
    web_thread.start()
    _brain_loop(state)


if __name__ == "__main__":
    main()
