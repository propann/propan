"""Backward-compatible entrypoint for HAL."""

from propan.hal import main
from propan.logging_utils import configure_logging


if __name__ == "__main__":
    configure_logging()
    main()
