"""One view, two audiences. FinOps and SecOps read the same numbers, from the same audit log."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Set

from .money import ZERO

UNREGISTERED = "<unregistered>"
_SECURITY_BLOCKS = (
    "BLOCK_IDENTITY",
    "BLOCK_QUARANTINE",
    "BLOCK_SCOPE",
    "BLOCK_CONTEXT",
    "BLOCK_RATE",
)
FOOTNOTE = (
    "Prices are illustrative. 'blocked' = what blocked calls WOULD have cost (counterfactual)."
)


def _dec(value: Optional[str]) -> Optional[Decimal]:
    return Decimal(value) if value is not None else None


def summarize(events: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate audit events into one summary row per agent.

    Calls from unregistered IDs are pooled into a single ``<unregistered>`` row so an
    attacker spraying random IDs cannot bloat the report.
    """
    rows: Dict[str, Dict[str, Any]] = {}
    ids: Dict[str, Set[str]] = {}
    for e in events:
        key = UNREGISTERED if e.get("decision") == "BLOCK_IDENTITY" else e["agent_id"]
        row = rows.setdefault(
            key,
            {
                "agent_id": key,
                "budget_usd": None,
                "spent_usd": ZERO,
                "allowed": 0,
                "blocked": 0,
                "security_blocks": 0,
                "budget_blocks": 0,
                "avoided_usd": ZERO,
                "routing_savings_usd": ZERO,
                "quarantined": False,
                "budget_warned": False,
            },
        )
        ids.setdefault(key, set()).add(e["agent_id"])

        if e.get("budget_usd") is not None:
            row["budget_usd"] = _dec(e["budget_usd"])
        if e.get("spent_usd") is not None:
            row["spent_usd"] = _dec(e["spent_usd"])
        row["quarantined"] = row["quarantined"] or bool(e.get("quarantined"))
        row["budget_warned"] = row["budget_warned"] or bool(e.get("budget_warned"))

        if e["event"] != "decision":
            continue
        if e["decision"] == "ALLOW":
            row["allowed"] += 1
            row["routing_savings_usd"] += Decimal(e["baseline_usd"]) - Decimal(e["cost_usd"])
        else:
            row["blocked"] += 1
            row["avoided_usd"] += Decimal(e["avoided_usd"])
            if e["decision"] in _SECURITY_BLOCKS:
                row["security_blocks"] += 1
            elif e["decision"] == "BLOCK_BUDGET":
                row["budget_blocks"] += 1

    for key, row in rows.items():
        row["distinct_ids"] = len(ids[key])
        row["status"] = _status(row)
    return rows


def _status(row: Dict[str, Any]) -> str:
    if row["quarantined"]:
        return "QUARANTINED"
    if row["security_blocks"]:
        return "ANOMALY"
    budget = row["budget_usd"]
    if budget is not None and row["spent_usd"] > budget:
        return "BUDGET_EXCEEDED"
    if row["budget_blocks"]:
        return "BUDGET_BLOCKED"
    if row["budget_warned"]:
        return "BUDGET_WARNING"
    return "OK"


def render(summary: Dict[str, Dict[str, Any]], width: int = 64) -> str:
    """Plain-text dashboard. No dependencies, works in any terminal or CI log."""
    bar = "=" * width
    lines: List[str] = [bar, "TOKENMAXXING-GUARD | UNIFIED FINOPS + SECOPS DASHBOARD", bar]
    if not summary:
        lines.append("No activity recorded yet.")
        return "\n".join(lines)

    for row in summary.values():
        budget = row["budget_usd"]
        used = f"${row['spent_usd']:.4f}" + (f" of ${budget:.2f}" if budget is not None else "")
        name = row["agent_id"]
        if name == UNREGISTERED:
            name += f" ({row['distinct_ids']} distinct IDs)"
        lines += [
            "",
            f"Agent   : {name}",
            f"Status  : {row['status']}",
            f"Spend   : {used}",
            f"Calls   : {row['allowed']} allowed, {row['blocked']} blocked "
            f"({row['security_blocks']} security, {row['budget_blocks']} budget)",
            f"Impact  : ${row['avoided_usd']:.4f} blocked  |  "
            f"${row['routing_savings_usd']:.4f} saved by routing",
        ]

    total_spent = sum((r["spent_usd"] for r in summary.values()), ZERO)
    total_avoided = sum((r["avoided_usd"] for r in summary.values()), ZERO)
    total_saved = sum((r["routing_savings_usd"] for r in summary.values()), ZERO)
    lines += [
        "",
        "-" * width,
        f"TOTAL spent ${total_spent:.4f} | blocked ${total_avoided:.4f} "
        f"| routing saved ${total_saved:.4f}",
        FOOTNOTE,
        bar,
    ]
    return "\n".join(lines)
