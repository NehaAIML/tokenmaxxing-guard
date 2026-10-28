#!/usr/bin/env python3
"""Regenerate (or --check) the demo dashboard block embedded in README.md.

python scripts/update_readme.py          # rewrite the block
python scripts/update_readme.py --check  # exit 1 if README is out of date (used by CI)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tokenmaxxing_guard.scenarios import (  # noqa: E402
    README_END,
    README_START,
    render_readme_block,
)


def main() -> int:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = text.find(README_START), text.find(README_END)
    if start == -1 or end == -1:
        print(f"README.md is missing the {README_START} / {README_END} markers", file=sys.stderr)
        return 2
    updated = text[:start] + render_readme_block() + text[end + len(README_END) :]
    if "--check" in sys.argv:
        if updated != text:
            print(
                "README demo block is stale. Run: python scripts/update_readme.py", file=sys.stderr
            )
            return 1
        print("README demo block is up to date.")
        return 0
    readme.write_text(updated, encoding="utf-8")
    print("README.md updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
