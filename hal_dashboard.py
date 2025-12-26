"""Backward-compatible entrypoint for HAL dashboard."""

from propan.hal_dashboard import main
from propan.logging_utils import configure_logging


if __name__ == "__main__":
    configure_logging()
    main()
