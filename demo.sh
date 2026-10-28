#!/usr/bin/env bash
# One command, no API key, no dependencies: watch the guard stop a runaway agent.
set -euo pipefail
cd "$(dirname "$0")"
PYTHONPATH=src python3 -m tokenmaxxing_guard demo --log audit.jsonl
echo
echo "Re-render the same dashboard from the audit trail:"
echo "  PYTHONPATH=src python3 -m tokenmaxxing_guard report audit.jsonl"
