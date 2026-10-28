"""The single control point where cost and security meet.

Every agent call passes through ``Guard.check`` *before* it reaches a model or tool.
Checks run in a fixed order (cheapest and most security-critical first) and every
attempt, allowed or blocked, is written to the audit log.
"""

from __future__ import annotations

import itertools
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

from .identity import AgentRecord, AgentRegistry
from .ledger import AuditLog
from .models import Decision, Verdict
from .policy import load_policy
from .router import Router

RATE_WINDOW_SECONDS = 60.0
_EPSILON = 1e-9  # float tolerance so spending exactly the budget is allowed


class Guard:
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        router: Optional[Router] = None,
        audit: Optional[AuditLog] = None,
        clock: Callable[[], float] = time.time,
        warn_ratio: float = 0.8,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.router = router or Router()
        self.audit = audit or AuditLog()
        self._clock = clock
        self.warn_ratio = warn_ratio
        self._ids = itertools.count(1)
        self._reservations: Dict[str, Tuple[str, str, float]] = {}

    @classmethod
    def from_policy(
        cls,
        path: Union[str, Path],
        audit: Optional[AuditLog] = None,
        clock: Callable[[], float] = time.time,
    ) -> Guard:
        registry, router = load_policy(path)
        return cls(registry=registry, router=router, audit=audit, clock=clock)

    # ------------------------------------------------------------------ public API

    def register(
        self, agent_id: str, allowed_tools: Iterable[str], budget_usd: float, **limits: Any
    ) -> AgentRecord:
        return self.registry.register(agent_id, allowed_tools, budget_usd, **limits)

    def check(
        self,
        agent_id: str,
        task_type: str,
        tool: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Verdict:
        """Decide whether this call may proceed. Reserves the projected cost on ALLOW."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must be >= 0")

        tier = self.router.route(task_type)
        projected = tier.cost(input_tokens, output_tokens)
        baseline = self.router.baseline_cost(input_tokens, output_tokens)
        call = dict(
            agent_id=agent_id,
            task_type=task_type,
            tool=tool,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            projected=projected,
            baseline=baseline,
            tier=tier.name,
        )

        # The lock makes check-then-reserve atomic, so concurrent calls cannot
        # each pass the budget check and collectively overspend.
        with self.registry.lock:
            agent = self.registry.get(agent_id)
            now = self._clock()

            if agent is None:
                return self._deny(None, Decision.BLOCK_IDENTITY, "unknown agent", call)

            if agent.quarantined:
                return self._deny(
                    agent,
                    Decision.BLOCK_QUARANTINE,
                    "agent is quarantined; operator release required",
                    call,
                )

            if tool not in agent.allowed_tools:
                agent.denial_streak += 1
                if agent.denial_streak >= agent.quarantine_after_denials:
                    agent.quarantined = True
                    agent.alerts.append(
                        f"QUARANTINED: {agent.denial_streak} consecutive out-of-scope tool calls "
                        f"(last: '{tool}')"
                    )
                return self._deny(
                    agent, Decision.BLOCK_SCOPE, f"tool '{tool}' not in allowed scope", call
                )

            if input_tokens > agent.max_input_tokens:
                return self._deny(
                    agent,
                    Decision.BLOCK_CONTEXT,
                    f"input {input_tokens:,} tokens exceeds cap {agent.max_input_tokens:,}",
                    call,
                )

            while agent.call_times and now - agent.call_times[0] >= RATE_WINDOW_SECONDS:
                agent.call_times.popleft()
            if len(agent.call_times) >= agent.max_calls_per_minute:
                return self._deny(
                    agent,
                    Decision.BLOCK_RATE,
                    f"more than {agent.max_calls_per_minute} calls per minute",
                    call,
                )

            if agent.spent_usd + projected > agent.budget_usd + _EPSILON:
                return self._deny(
                    agent,
                    Decision.BLOCK_BUDGET,
                    f"projected ${projected:.4f} would exceed budget "
                    f"${agent.budget_usd:.2f} (spent ${agent.spent_usd:.4f})",
                    call,
                )

            # ALLOW: reserve spend, reset the violation streak, record the timestamp.
            agent.spent_usd += projected
            agent.allowed_calls += 1
            agent.denial_streak = 0
            agent.call_times.append(now)
            if not agent.budget_warned and agent.spent_usd >= agent.budget_usd * self.warn_ratio:
                agent.budget_warned = True
                agent.alerts.append(
                    f"BUDGET_WARNING: {agent.spent_usd / agent.budget_usd:.0%} of "
                    f"${agent.budget_usd:.2f} used"
                    if agent.budget_usd
                    else "BUDGET_WARNING: zero budget"
                )

            call_id = f"call-{next(self._ids):06d}"
            self._reservations[call_id] = (agent_id, task_type, projected)
            verdict = Verdict(
                Decision.ALLOW,
                "ok",
                agent_id,
                tool,
                tier=tier.name,
                cost_usd=projected,
                call_id=call_id,
            )
            self._log(agent, verdict, call, charged=projected, avoided=0.0)
            return verdict

    def settle(self, call_id: str, actual_input_tokens: int, actual_output_tokens: int) -> float:
        """Replace a call's estimated cost with the real token usage reported by the provider.

        Returns the correction applied (actual - estimated). Call this after the model responds.
        """
        with self.registry.lock:
            agent_id, task_type, reserved = self._reservations.pop(call_id)
            agent = self.registry.get(agent_id)
            if agent is None:  # pragma: no cover - reservations only exist for known agents
                raise KeyError(agent_id)
            actual = self.router.estimate_cost(task_type, actual_input_tokens, actual_output_tokens)
            delta = actual - reserved
            agent.spent_usd += delta
            self.audit.record(
                {
                    "event": "settle",
                    "ts": self._iso(),
                    "agent_id": agent_id,
                    "call_id": call_id,
                    "cost_usd": round(actual, 6),
                    "delta_usd": round(delta, 6),
                    "budget_usd": agent.budget_usd,
                    "spent_usd": round(agent.spent_usd, 6),
                    "quarantined": agent.quarantined,
                }
            )
            return delta

    # ------------------------------------------------------------------ internals

    def _deny(
        self, agent: Optional[AgentRecord], decision: Decision, reason: str, call: Dict[str, Any]
    ) -> Verdict:
        if agent is not None:
            agent.blocked_calls += 1
        verdict = Verdict(decision, reason, call["agent_id"], call["tool"])
        # avoided = what this call would have cost had the guard not stopped it
        self._log(agent, verdict, call, charged=0.0, avoided=call["projected"])
        return verdict

    def _log(
        self,
        agent: Optional[AgentRecord],
        verdict: Verdict,
        call: Dict[str, Any],
        charged: float,
        avoided: float,
    ) -> None:
        self.audit.record(
            {
                "event": "decision",
                "ts": self._iso(),
                "agent_id": call["agent_id"],
                "tool": call["tool"],
                "task_type": call["task_type"],
                "decision": verdict.decision.value,
                "reason": verdict.reason,
                "tier": call["tier"],
                "input_tokens": call["input_tokens"],
                "output_tokens": call["output_tokens"],
                "cost_usd": round(charged, 6),
                "avoided_usd": round(avoided, 6),
                "baseline_usd": round(call["baseline"], 6) if verdict.allowed else 0.0,
                "call_id": verdict.call_id,
                "budget_usd": agent.budget_usd if agent else None,
                "spent_usd": round(agent.spent_usd, 6) if agent else None,
                "quarantined": agent.quarantined if agent else False,
            }
        )

    def _iso(self) -> str:
        return datetime.fromtimestamp(self._clock(), tz=timezone.utc).isoformat(timespec="seconds")
