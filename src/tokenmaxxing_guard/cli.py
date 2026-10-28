"""Command line entry point: ``tokenmaxxing-guard demo`` and ``tokenmaxxing-guard report``."""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from . import __version__
from .dashboard import render, summarize
from .ledger import read_events
from .scenarios import run_demo


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tokenmaxxing-guard",
        description="Unified FinOps + SecOps guardrails for AI agents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the built-in tokenmaxxing scenario")
    demo.add_argument("--log", help="also write the audit trail to this JSONL file")

    report = sub.add_parser("report", help="render a dashboard from an audit log")
    report.add_argument("log", help="path to a JSONL audit log")
    report.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    args = parser.parse_args(argv)
    if args.command == "demo":
        run_demo(args.log)
        return 0

    summary = summarize(read_events(args.log))
    print(json.dumps(summary, indent=2, default=str) if args.json else render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
