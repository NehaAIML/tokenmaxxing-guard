"""Append-only audit log. Every decision is recorded, especially the blocked ones."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class AuditLog:
    """In-memory event list with optional JSON Lines persistence."""

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self.path = Path(path) if path else None
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self.events.append(event)
            if self.path:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(event, sort_keys=True) + "\n")


def read_events(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load events from a JSON Lines audit file, skipping blank lines."""
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
