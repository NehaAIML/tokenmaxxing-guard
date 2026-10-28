# Contributing

Thanks for helping. This project is small on purpose: zero runtime dependencies and one control point.

## Setup

```bash
git clone https://github.com/NehaAIML/tokenmaxxing-guard && cd tokenmaxxing-guard
python -m venv .venv && source .venv/bin/activate
make install        # editable install + dev tools
make all            # lint + types + tests; must pass before a PR
./demo.sh           # sanity check
```

## Ground rules

1. **Every new check needs a test for the blocked path**, not only the happy path.
2. **Every decision, allowed or blocked, must reach the audit log.** A silent block is a bug.
3. **No runtime dependencies** without a discussion first.
4. **Fail closed.** If you are unsure whether to allow, block and say why.
5. If you change demo output, run `python scripts/update_readme.py` (a test enforces this).
6. Update `CHANGELOG.md` (Unreleased) and the README/docs if a decision code, config key or CLI flag changes.

## Commit style

[Conventional Commits](https://www.conventionalcommits.org): `feat:`, `fix:`, `docs:`, `test:`, `chore:`.

## Code of conduct

Be kind and assume good faith. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
