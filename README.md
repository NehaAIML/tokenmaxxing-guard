
<div align="center">

# 🛡️ tokenmaxxing-guard

**See an AI agent get blocked in 60 seconds.**
*Unified FinOps + SecOps guardrails for autonomous agents. No API key needed.*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)]()

</div>

---

## 💸 The Problem

Agents burn tokens in loops, inherit broad service-account permissions, and the invoice arrives *after* the damage is done. FinOps watches the bill; SecOps watches the permissions; both are reading the same API logs in different languages, so a runaway agent looks like "a cost problem" to one team and "an access problem" to the other, and nobody owns it.

> *The invoice tells you what happened. This guard decides before it happens.*

---

## ⚡ The 60-Second Demo

Run the script. Watch the guard block a runaway agent loop.

```text
$ ./demo.sh

[1] code-review-bot: read-only agent keeps trying to write files
    call 01: BLOCK_SCOPE       tool 'write_file' not in allowed scope
    ...
    call 06: BLOCK_QUARANTINE  agent is quarantined; operator release required
    ...

================================================================
TOKENMAXXING-GUARD | UNIFIED FINOPS + SECOPS DASHBOARD
================================================================

Agent   : code-review-bot
Status  : QUARANTINED
Spend   : $0.0000 of $5.00
Calls   : 0 allowed, 12 blocked (12 security, 0 budget)
Avoided : $2.5500 blocked  |  $0.0000 saved by routing

Agent   : summarizer-bot
Status  : OK
Spend   : $0.0105 of $2.00
Calls   : 10 allowed, 0 blocked
Avoided : $0.0000 blocked  |  $0.5145 saved by routing

Agent   : runaway-planner
Status  : BUDGET_BLOCKED
Spend   : $1.0000 of $1.00
Calls   : 5 allowed, 3 blocked (0 security, 3 budget)
Avoided : $0.6000 blocked  |  $0.0000 saved by routing
================================================================
