python3 -c "
content = '''<div align=\"center\">

# 🛡️ tokenmaxxing-guard

**See an AI agent get blocked in 60 seconds.**
*Unified FinOps + SecOps guardrails for autonomous agents. No API key needed.*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)]()

</div>

---

## 💸 The Problem

Agents burn tokens in loops, inherit service-account permissions, and the invoice arrives *after* the damage is done. Uber burned its 2026 AI budget by April. Microsoft told engineers to stop \"tokenmaxxing\" in July. 

The problem is not that engineers use too much AI. The problem is that **FinOps and SecOps are looking at the same API logs and speaking different languages.**

> *The invoice tells you what happened. This guard tells you before it happens.*

---

## 🏗️ The Architecture

Most companies build the cost layer and ignore the security layer. This repo shows why they must be the same layer. 

\`\`\`text
       [ PROMPT / TASK ]
               │
               ▼
     ┌───────────────────┐
     │     guard.py      │ ◄─── The Intersection
     │ (Unified Control) │
     └─────────┬─────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│  router.py  │ │ identity.py │
│   (FinOps)  │ │  (SecOps)   │
├─────────────┤ ├─────────────┤
│ Route cheap │ │ Unique ID   │
│ Route front │ │ Least priv. │
│ Save $$$    │ │ Block loops │
└─────────────┘ └─────────────┘
       │               │
       └───────┬───────┘
               ▼
     ┌───────────────────┐
     │   dashboard.py    │ ◄─── Unified View
     │  (One Dashboard)  │
     └───────────────────┘
\`\`\`

- **\`router.py\`** (FinOps) — Routes simple tasks to a small model (50x cheaper) and complex tasks to a frontier model.
- **\`identity.py\`** (SecOps) — Assigns unique identities to agents and enforces least-privilege tool access.
- **\`guard.py\`** (The Intersection) — The single control point. It checks budget, identity, and behavior *before* the model is called.
- **\`dashboard.py\`** (Unified View) — FinOps and SecOps read the same telemetry.

---

## ⚡ The 60-Second Demo

Run the script. Watch the guard block a runaway agent loop. 

\`\`\`text
$ ./demo.sh

============================================================
  TOKENMAXXING-GUARD DEMO
  Unified FinOps + SecOps guardrails for AI agents
============================================================

Registering \'code-review-bot\' with read-only access and $5.00 budget...
Simulating tokenmaxxing loop...

Call 01: BLOCK_IDENTITY — tool \'write_file\' not in allowed scope
Call 02: BLOCK_IDENTITY — tool \'write_file\' not in allowed scope
Call 03: BLOCK_IDENTITY — tool \'write_file\' not in allowed scope
...
Call 12: BLOCK_IDENTITY — tool \'write_file\' not in allowed scope

============================================================
TOKENMAXXING-GUARD | UNIFIED FINOPS + SECOPS DASHBOARD
============================================================

Agent: code-review-bot
  Budget:  $5.00
  Spent:   $0.0000
  Calls:   0
  Status:  OK

============================================================
\`\`\`

The agent tried to call a write tool in a loop with a bloated 40,000-token context. The guard blocked it at the identity layer. **No tokens were burned. No budget was exceeded.**

---

## 🚀 How to Run It

Clone the repo and run the demo. No external dependencies (stdlib only).

\`\`\`bash
git clone https://github.com/NehaAIML/tokenmaxxing-guard.git
cd tokenmaxxing-guard
./demo.sh
\`\`\`

*(If you get a \"permission denied\" error on Mac/Linux, run \`chmod +x demo.sh\` first, then \`./demo.sh\`).*

---

## 🧠 Why This Exists

Tokenmaxxing is a governance failure, not an engineering one. The goal of this repo is to show the minimum viable control point where cost and security converge. 

If you are a CTO, CISO, or FinOps lead trying to get agents under control, this is the architectural pattern you need: **build the inventory before you build the cap.**

*Built by [Neha Purohit](https://github.com/NehaAIML). Read the full article for the deep dive on why the invoice is a lagging indicator.*
'''
with open('README.md', 'w') as f:
    f.write(content)
print('README.md successfully overwritten!')

