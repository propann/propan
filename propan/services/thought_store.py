"""In-memory storage for HAL thoughts."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Thought:
    """Represents a single HAL thought entry."""

    text: str
    source: str
    created_at: str


class ThoughtStore:
    """Keeps a bounded history of thoughts in memory."""

    def __init__(self, max_items: int = 50) -> None:
        self._items: deque[Thought] = deque(maxlen=max_items)

    def add(self, text: str, source: str = "system") -> Thought:
        """Add a new thought and return it."""
        timestamp = datetime.now(timezone.utc).isoformat()
        thought = Thought(text=text, source=source, created_at=timestamp)
        self._items.append(thought)
        return thought

    def list(self) -> list[dict[str, str]]:
        """Return all thoughts as serializable dictionaries."""
        return [asdict(item) for item in self._items]

    def latest(self) -> dict[str, str] | None:
        """Return the latest thought as a dict."""
        if not self._items:
            return None
        return asdict(self._items[-1])

    def clear(self) -> None:
        """Remove all stored thoughts."""
        self._items.clear()

    def __iter__(self) -> Iterable[Thought]:
        return iter(self._items)
