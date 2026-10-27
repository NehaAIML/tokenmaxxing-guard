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

Agents burn tokens in loops, inherit service-account permissions, and the invoice arrives *after* the damage is done. Uber burned its 2026 AI budget by April. Microsoft told engineers to stop "tokenmaxxing" in July. 

The problem is not that engineers use too much AI. The problem is that **FinOps and SecOps are looking at the same API logs and speaking different languages.**

> *The invoice tells you what happened. This guard tells you before it happens.*

---

## 🏗️ The Architecture

Most companies build the cost layer and ignore the security layer. This repo shows why they must be the same layer. 

```text
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
