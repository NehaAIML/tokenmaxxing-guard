import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_license_exists():
    """The LICENSE file must exist and look like an MIT license."""
    license_path = ROOT / "LICENSE"
    assert license_path.exists(), "LICENSE file is missing"
    content = license_path.read_text()
    assert "MIT License" in content

def test_markdown_links_are_valid():
    """Every relative Markdown link in the README must point to an existing file."""
    readme = (ROOT / "README.md").read_text()
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', readme)
    for link in links:
        if link.startswith("http") or link.startswith("#"):
            continue
        target = ROOT / link
        assert target.exists(), f"Markdown link points to missing file: {link}"
