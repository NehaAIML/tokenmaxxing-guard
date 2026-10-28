# Security policy

This project is a **reference implementation and demo**, not a hardened production gateway. Read
[docs/threat-model.md](docs/threat-model.md) for what it does and does not defend against.

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Use GitHub's private reporting:
**Security tab → Report a vulnerability**. Include a minimal reproduction and the version.

You can expect an acknowledgement within 7 days. Fixes for confirmed issues are released with a
CHANGELOG entry and credit (unless you prefer otherwise).

## Supported versions

| Version | Supported |
|---|---|
| 0.2.1 and later | yes |
| 0.2.0 | no (quarantine could be evaded by interleaving legal calls) |
| 0.1.x | no (blocked calls were not recorded) |
