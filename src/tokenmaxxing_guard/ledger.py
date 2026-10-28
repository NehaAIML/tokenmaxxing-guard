"""Append-only audit log. Every decision is recorded, especially the blocked ones."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class AuditLog:
    """In-memory event list with optional JSON Lines persistence.

    Each event is written as ONE ``write`` on an ``O_APPEND`` descriptor, so independent
    writers (threads, or processes on the same local filesystem) cannot interleave
    partial lines. This is not a substitute for a real log pipeline: ship the file to
    write-once storage or a SIEM in production.
    """

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self.path = Path(path) if path else None
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self.events.append(event)
            if self.path:
                line = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
                fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
                try:
                    os.write(fd, line)
                finally:
                    os.close(fd)


def read_events(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load events from a JSON Lines audit file, skipping blank lines."""
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
