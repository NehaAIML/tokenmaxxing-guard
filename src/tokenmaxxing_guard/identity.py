"""SecOps: unique agent identities, least-privilege scopes, and per-agent state."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, FrozenSet, Iterable, List, Optional


@dataclass
class AgentRecord:
    """Identity + policy + live counters for one agent."""

    agent_id: str
    allowed_tools: FrozenSet[str]
    budget_usd: float
    max_input_tokens: int = 32_000
    max_calls_per_minute: int = 60
    quarantine_after_denials: int = 5

    spent_usd: float = 0.0
    allowed_calls: int = 0
    blocked_calls: int = 0
    denial_streak: int = 0
    quarantined: bool = False
    budget_warned: bool = False
    alerts: List[str] = field(default_factory=list)
    call_times: Deque[float] = field(default_factory=deque)


class AgentRegistry:
    """Thread-safe store of agent identities. No shared service accounts, no inherited rights."""

    def __init__(self) -> None:
        self._agents: Dict[str, AgentRecord] = {}
        self.lock = threading.RLock()

    def register(
        self,
        agent_id: str,
        allowed_tools: Iterable[str],
        budget_usd: float,
        *,
        max_input_tokens: int = 32_000,
        max_calls_per_minute: int = 60,
        quarantine_after_denials: int = 5,
    ) -> AgentRecord:
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")
        if budget_usd < 0:
            raise ValueError("budget_usd must be >= 0")
        if max_input_tokens <= 0 or max_calls_per_minute <= 0 or quarantine_after_denials <= 0:
            raise ValueError("limits must be positive integers")
        with self.lock:
            if agent_id in self._agents:
                raise ValueError(f"agent '{agent_id}' is already registered")
            record = AgentRecord(
                agent_id=agent_id,
                allowed_tools=frozenset(allowed_tools),
                budget_usd=float(budget_usd),
                max_input_tokens=max_input_tokens,
                max_calls_per_minute=max_calls_per_minute,
                quarantine_after_denials=quarantine_after_denials,
            )
            self._agents[agent_id] = record
            return record

    def get(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.get(agent_id)

    def all(self) -> List[AgentRecord]:
        with self.lock:
            return list(self._agents.values())

    def release(self, agent_id: str) -> None:
        """Manually lift a quarantine. Deliberately a human/operator action, never automatic."""
        with self.lock:
            record = self._agents[agent_id]
            record.quarantined = False
            record.denial_streak = 0
            record.alerts.append("RELEASED: quarantine lifted by operator")
