"""Shared value types."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from .money import ZERO


class Decision(str, Enum):
    """Outcome of a guard check. Anything other than ALLOW means the call must not proceed."""

    ALLOW = "ALLOW"
    BLOCK_IDENTITY = "BLOCK_IDENTITY"  # agent is not registered
    BLOCK_QUARANTINE = "BLOCK_QUARANTINE"  # auto-quarantined after repeated violations
    BLOCK_SCOPE = "BLOCK_SCOPE"  # tool is outside the agent's least-privilege scope
    BLOCK_CONTEXT = "BLOCK_CONTEXT"  # input context exceeds the per-call token cap
    BLOCK_RATE = "BLOCK_RATE"  # too many calls in the sliding window
    BLOCK_BUDGET = "BLOCK_BUDGET"  # projected spend would exceed the agent's budget


@dataclass(frozen=True)
class Verdict:
    """What the guard decided, and why."""

    decision: Decision
    reason: str
    agent_id: str
    tool: str
    tier: Optional[str] = None
    cost_usd: Decimal = ZERO
    call_id: Optional[str] = None

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW
