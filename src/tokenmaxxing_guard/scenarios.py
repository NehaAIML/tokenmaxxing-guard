"""Built-in demo: three agents, three behaviours. No API key, no network."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Union

from .dashboard import render, summarize
from .guard import Guard
from .ledger import AuditLog

README_START = "<!-- demo:start -->"
README_END = "<!-- demo:end -->"


def run_demo(
    log_path: Optional[Union[str, Path]] = None,
    out: Callable[[str], None] = print,
) -> Guard:
    guard = Guard(audit=AuditLog(log_path))

    guard.register("code-review-bot", ["read_file", "list_files"], budget_usd="5.00")
    guard.register("summarizer-bot", ["read_file"], budget_usd="2.00")
    guard.register("runaway-planner", ["read_file", "search"], budget_usd="1.00")

    out("\n[1] code-review-bot: read-only agent keeps trying to write files")
    for i in range(1, 13):
        v = guard.check("code-review-bot", "debug_complex", "write_file", 40_000, 500)
        out(f"    call {i:02d}: {v.decision.value:<17} {v.reason}")

    out("\n[2] summarizer-bot: well-behaved agent, cheap tier")
    for i in range(1, 11):
        v = guard.check("summarizer-bot", "summarize", "read_file", 8_000, 500)
        if i in (1, 10):
            out(f"    call {i:02d}: {v.decision.value:<17} tier={v.tier} cost=${v.cost_usd:.5f}")

    out("\n[3] runaway-planner: allowed tools, but loops on expensive frontier calls")
    for i in range(1, 9):
        v = guard.check("runaway-planner", "architecture", "search", 20_000, 4_000)
        detail = f"cost=${v.cost_usd:.4f}" if v.allowed else v.reason
        out(f"    call {i:02d}: {v.decision.value:<17} {detail}")

    out("")
    out(render(summarize(guard.audit.events)))
    if log_path:
        out(f"\nAudit log written to {log_path}")
    return guard


def render_readme_block() -> str:
    """The exact dashboard text embedded in README.md. A test fails if it drifts."""
    guard = run_demo(out=lambda _line: None)
    dashboard = render(summarize(guard.audit.events))
    return f"{README_START}\n```text\n{dashboard}\n```\n{README_END}"
