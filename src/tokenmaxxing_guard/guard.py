"""The single control point where cost and security meet.

Every agent call passes through ``Guard.check`` *before* it reaches a model or tool.
Checks run in a fixed order (cheapest and most security-critical first) and every
attempt, allowed or blocked, is written to the audit log.
"""

from __future__ import annotations

import itertools
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, Optional, Tuple, Union

from .identity import BUDGET_WARN_RATIO, AgentRecord, AgentRegistry
from .ledger import AuditLog
from .models import Decision, Verdict
from .money import Number, quantize, to_decimal
from .policy import load_policy
from .router import Router

RATE_WINDOW_SECONDS = 60.0


def _prune(times: Deque[float], now: float, window: float) -> None:
    """Drop timestamps that have aged out of a sliding window."""
    while times and now - times[0] >= window:
        times.popleft()


def _m(value: Decimal) -> str:
    """Money as a fixed-point string for the audit log (JSON has no Decimal)."""
    return str(quantize(value))


class Guard:
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        router: Optional[Router] = None,
        audit: Optional[AuditLog] = None,
        clock: Callable[[], float] = time.time,
        warn_ratio: Number = BUDGET_WARN_RATIO,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.router = router or Router()
        self.audit = audit or AuditLog()
        self._clock = clock
        self.warn_ratio = to_decimal(warn_ratio)
        self._ids = itertools.count(1)
        self._reservations: Dict[str, Tuple[str, str, Decimal]] = {}

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
        self, agent_id: str, allowed_tools: Iterable[str], budget_usd: Number, **limits: Any
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
        call: Dict[str, Any] = {
            "agent_id": agent_id,
            "task_type": task_type,
            "tool": tool,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "projected": tier.cost(input_tokens, output_tokens),
            "baseline": self.router.baseline_cost(input_tokens, output_tokens),
            "tier": tier.name,
        }
        projected: Decimal = call["projected"]

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
                # Violations are counted in a SLIDING WINDOW, not a consecutive streak,
                # so interleaving legal calls cannot reset the counter.
                agent.violation_times.append(now)
                _prune(agent.violation_times, now, agent.quarantine_window_seconds)
                count = len(agent.violation_times)
                if count >= agent.quarantine_after_denials:
                    agent.quarantined = True
                    agent.alerts.append(
                        f"QUARANTINED: {count} out-of-scope tool calls within "
                        f"{agent.quarantine_window_seconds:g}s (last: '{tool}')"
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

            _prune(agent.call_times, now, RATE_WINDOW_SECONDS)
            if len(agent.call_times) >= agent.max_calls_per_minute:
                return self._deny(
                    agent,
                    Decision.BLOCK_RATE,
                    f"more than {agent.max_calls_per_minute} calls per minute",
                    call,
                )

            if agent.spent_usd + projected > agent.budget_usd:
                return self._deny(
                    agent,
                    Decision.BLOCK_BUDGET,
                    f"projected ${projected:.4f} would exceed budget "
                    f"${agent.budget_usd:.2f} (spent ${agent.spent_usd:.4f})",
                    call,
                )

            # ALLOW: reserve spend and record the timestamp.
            agent.spent_usd += projected
            agent.allowed_calls += 1
            agent.call_times.append(now)
            if (
                not agent.budget_warned
                and agent.budget_usd > 0
                and agent.spent_usd >= agent.budget_usd * self.warn_ratio
            ):
                agent.budget_warned = True
                agent.alerts.append(
                    f"BUDGET_WARNING: {agent.spent_usd / agent.budget_usd:.0%} of "
                    f"${quantize(agent.budget_usd)} used"
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
            self._log(agent, verdict, call, charged=projected, avoided=Decimal(0))
            return verdict

    def settle(self, call_id: str, actual_input_tokens: int, actual_output_tokens: int) -> Decimal:
        """Replace a call's estimated cost with the real token usage reported by the provider.

        Returns the correction applied (actual - estimated). Call this after the model responds.
        If real usage pushes the agent over budget, an OVERRUN alert is raised: the call has
        already happened, so the guard can only report it and block the *next* one.
        """
        with self.registry.lock:
            agent_id, task_type, reserved = self._reservations.pop(call_id)
            agent = self.registry.get(agent_id)
            if agent is None:  # pragma: no cover - reservations only exist for known agents
                raise KeyError(agent_id)
            actual = self.router.estimate_cost(task_type, actual_input_tokens, actual_output_tokens)
            delta = actual - reserved
            agent.spent_usd += delta
            if agent.spent_usd > agent.budget_usd and not agent.overrun_flagged:
                agent.overrun_flagged = True
                agent.alerts.append(
                    f"OVERRUN: spent ${quantize(agent.spent_usd)} exceeds budget "
                    f"${quantize(agent.budget_usd)} after settlement"
                )
            self.audit.record(
                {
                    "event": "settle",
                    "ts": self._iso(),
                    "agent_id": agent_id,
                    "call_id": call_id,
                    "cost_usd": _m(actual),
                    "delta_usd": _m(delta),
                    "budget_usd": _m(agent.budget_usd),
                    "spent_usd": _m(agent.spent_usd),
                    "quarantined": agent.quarantined,
                    "budget_warned": agent.budget_warned,
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
        # "avoided" = what this call WOULD have cost had the guard not stopped it (counterfactual)
        self._log(agent, verdict, call, charged=Decimal(0), avoided=call["projected"])
        return verdict

    def _log(
        self,
        agent: Optional[AgentRecord],
        verdict: Verdict,
        call: Dict[str, Any],
        charged: Decimal,
        avoided: Decimal,
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
                "cost_usd": _m(charged),
                "avoided_usd": _m(avoided),
                "baseline_usd": _m(call["baseline"]) if verdict.allowed else _m(Decimal(0)),
                "call_id": verdict.call_id,
                "budget_usd": _m(agent.budget_usd) if agent else None,
                "spent_usd": _m(agent.spent_usd) if agent else None,
                "quarantined": agent.quarantined if agent else False,
                "budget_warned": agent.budget_warned if agent else False,
            }
        )

    def _iso(self) -> str:
        return datetime.fromtimestamp(self._clock(), tz=timezone.utc).isoformat(timespec="seconds")
