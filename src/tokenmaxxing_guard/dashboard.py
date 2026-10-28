"""One view, two audiences. FinOps and SecOps read the same numbers, from the same audit log."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

_BLOCKS = ("BLOCK_IDENTITY", "BLOCK_QUARANTINE", "BLOCK_SCOPE", "BLOCK_CONTEXT", "BLOCK_RATE")


def summarize(events: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate audit events into one summary row per agent."""
    rows: Dict[str, Dict[str, Any]] = {}
    for e in events:
        row = rows.setdefault(
            e["agent_id"],
            {
                "agent_id": e["agent_id"],
                "budget_usd": None,
                "spent_usd": 0.0,
                "allowed": 0,
                "blocked": 0,
                "security_blocks": 0,
                "budget_blocks": 0,
                "avoided_usd": 0.0,
                "routing_savings_usd": 0.0,
                "quarantined": False,
            },
        )
        if e.get("budget_usd") is not None:
            row["budget_usd"] = e["budget_usd"]
        if e.get("spent_usd") is not None:
            row["spent_usd"] = e["spent_usd"]
        row["quarantined"] = row["quarantined"] or bool(e.get("quarantined"))

        if e["event"] != "decision":
            continue
        if e["decision"] == "ALLOW":
            row["allowed"] += 1
            row["routing_savings_usd"] += e["baseline_usd"] - e["cost_usd"]
        else:
            row["blocked"] += 1
            row["avoided_usd"] += e["avoided_usd"]
            if e["decision"] in _BLOCKS:
                row["security_blocks"] += 1
            elif e["decision"] == "BLOCK_BUDGET":
                row["budget_blocks"] += 1

    for row in rows.values():
        row["status"] = _status(row)
    return rows


def _status(row: Dict[str, Any]) -> str:
    if row["quarantined"]:
        return "QUARANTINED"
    if row["security_blocks"]:
        return "ANOMALY"
    if row["budget_blocks"]:
        return "BUDGET_BLOCKED"
    if row["budget_usd"] and row["spent_usd"] >= 0.8 * row["budget_usd"]:
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
        lines += [
            "",
            f"Agent   : {row['agent_id']}",
            f"Status  : {row['status']}",
            f"Spend   : {used}",
            f"Calls   : {row['allowed']} allowed, {row['blocked']} blocked "
            f"({row['security_blocks']} security, {row['budget_blocks']} budget)",
            f"Avoided : ${row['avoided_usd']:.4f} blocked  |  "
            f"${row['routing_savings_usd']:.4f} saved by routing",
        ]

    total_spent = sum(r["spent_usd"] for r in summary.values())
    total_avoided = sum(r["avoided_usd"] for r in summary.values())
    total_saved = sum(r["routing_savings_usd"] for r in summary.values())
    lines += [
        "",
        "-" * width,
        f"TOTAL spent ${total_spent:.4f} | blocked ${total_avoided:.4f} "
        f"| routing saved ${total_saved:.4f}",
        bar,
    ]
    return "\n".join(lines)
