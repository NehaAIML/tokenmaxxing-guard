# 🛡️ tokenmaxxing-guard

**Watch an AI agent get stopped in 60 seconds. No API key, no dependencies.**
Unified FinOps + SecOps guardrails for autonomous agents: one control point for *what an agent may
spend* and *what an agent may do*.

---

## The problem

Agents burn tokens in loops, inherit broad service-account permissions, and the invoice arrives
*after* the damage is done. FinOps watches the bill; SecOps watches the permissions; both are
reading the same API logs in different languages, so a runaway agent looks like "a cost problem" to
one team and "an access problem" to the other, and nobody owns it.

> **The invoice tells you what happened. This guard decides before it happens.**

## Quickstart

```bash
git clone https://github.com/NehaAIML/tokenmaxxing-guard && cd tokenmaxxing-guard
./demo.sh
