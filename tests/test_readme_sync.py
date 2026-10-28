from pathlib import Path

from tokenmaxxing_guard.scenarios import README_END, README_START, render_readme_block

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_demo_block_matches_real_output():
    """If this fails, run: python scripts/update_readme.py"""
    text = README.read_text(encoding="utf-8")
    assert README_START in text and README_END in text, "README is missing the demo markers"
    assert render_readme_block() in text, "README demo output is stale"
