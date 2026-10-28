# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.1]

### Fixed
- Restored the `LICENSE` file, which was accidentally deleted in the v0.2.1 commit.
- Fixed the `mypy` configuration to be portable across different folder names.
- Added `tests/test_repo_hygiene.py` to fail if `LICENSE` is missing or Markdown links break.

### Security
- **Quarantine evasion fixed.** 0.2.0 counted a consecutive streak that reset on every allowed call, so an agent alternating one legal and one illegal call was never quarantined. Violations are now counted in a sliding window (`quarantine_after_denials` within `quarantine_window_seconds`, default 5 in 600 s).

### Changed
- **Money is exact.** All costs, prices and budgets use `Decimal` (new `money.py`). Audit events store money as fixed-point strings. `Verdict.cost_usd` and `Guard.settle()` now return `Decimal`.
- The 80% budget-warning threshold has a single source (`BUDGET_WARN_RATIO`); the dashboard reads the guard's `budget_warned` flag instead of duplicating the number.
- Dashboard "Avoided" renamed "Impact ... blocked" with a footnote: blocked dollars are a counterfactual and prices are illustrative.

### Added
- `OVERRUN` alert and `BUDGET_EXCEEDED` dashboard status when `settle()` shows real usage above budget.
- Audit log writes each event as a single `O_APPEND` write, so independent writers cannot interleave lines.
- Unregistered agent IDs are pooled into one `<unregistered>` dashboard row.
- README demo block is generated from real output (`scripts/update_readme.py`); a test and CI step fail if it drifts.
- Regression tests for every item above.

## [0.2.0]

### Fixed
- **Blocked calls are now recorded.** In 0.1 only allowed calls updated agent state, so an agent
  that was blocked 12 times still showed `Status: OK`, `Calls: 0` on the dashboard.
- `ALERT_ANOMALY` at >50 calls was a permanent lockout in disguise (the counter never moved again)
  and had no time window. Replaced by a real sliding-window `BLOCK_RATE`.

### Added
- `src/` package layout, `pyproject.toml`, `tokenmaxxing-guard` CLI (`demo`, `report`).
- `Guard` class with injectable clock, atomic check-and-reserve, and `settle()` for real usage.
- Automatic quarantine after N consecutive out-of-scope calls; manual `release()`.
- Per-call context cap (`BLOCK_CONTEXT`) and calls-per-minute limit (`BLOCK_RATE`).
- JSONL audit log; dashboard computed from the log; "avoided spend" and "routing savings" figures.
- JSON policy file support; examples; 28 tests (97% coverage); strict mypy; ruff; CI matrix 3.9 to 3.13.
- Docs: architecture (Mermaid), threat model; SECURITY, CONTRIBUTING, CODE_OF_CONDUCT.

### Changed
- Unknown task types fall back to a *configurable* `default_tier` (was hard-coded).
- `BLOCK_IDENTITY` is now only for unknown agents; out-of-scope tools return `BLOCK_SCOPE`.
- Breaking: module-level functions (`guarded_call`, `register_agent`) replaced by `Guard`/`AgentRegistry`.

## [0.1.0]
- Initial minimal demo.

[Unreleased]: https://github.com/NehaAIML/tokenmaxxing-guard/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/NehaAIML/tokenmaxxing-guard/releases/tag/v0.2.1
[0.2.0]: https://github.com/NehaAIML/tokenmaxxing-guard/releases/tag/v0.2.0
