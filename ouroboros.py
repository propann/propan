"""Backward-compatible entrypoint for Ouroboros."""

from propan.logging_utils import configure_logging
from propan.ouroboros import main


if __name__ == "__main__":
    configure_logging()
    main()
