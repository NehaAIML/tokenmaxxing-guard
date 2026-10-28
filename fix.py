import os
import re
from pathlib import Path

# 1. Restore the LICENSE file
license_content = """MIT License

Copyright (c) 2026 NehaAIML

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
with open("LICENSE", "w") as f:
    f.write(license_content)
print("Restored LICENSE")

# 2. Fix pyproject.toml mypy config
pyproject = Path("pyproject.toml")
content = pyproject.read_text()
content = content.replace('files = ["src"]', 'files = ["src/tokenmaxxing_guard"]')
pyproject.write_text(content)
print("Fixed mypy config")

# 3. Update CHANGELOG.md
changelog = Path("CHANGELOG.md")
content = changelog.read_text()
fix_header = """## [0.2.1]

### Fixed
- Restored the `LICENSE` file, which was accidentally deleted in the v0.2.1 commit.
- Fixed the `mypy` configuration to be portable across different folder names.
- Added `tests/test_repo_hygiene.py` to fail if `LICENSE` is missing or Markdown links break.

### Security"""
content = content.replace("## [0.2.1]\n\n### Security", fix_header)
changelog.write_text(content)
print("Updated CHANGELOG")

# 4. Create repo hygiene test
os.makedirs("tests", exist_ok=True)
hygiene_test = '''import re
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
    links = re.findall(r'\\[[^\\]]+\\]\\(([^)]+)\\)', readme)
    for link in links:
        if link.startswith("http") or link.startswith("#"):
            continue
        target = ROOT / link
        assert target.exists(), f"Markdown link points to missing file: {link}"
'''
with open("tests/test_repo_hygiene.py", "w") as f:
    f.write(hygiene_test)
print("Created test_repo_hygiene.py")

print("All fixes applied successfully!")
