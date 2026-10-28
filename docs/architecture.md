# Architecture

`tokenmaxxing-guard` puts **one control point** between an agent and anything that costs money or
has side effects. FinOps and SecOps are not two systems that get reconciled later; they are two
kinds of check in the same function, writing to the same audit log.

## Component view

```mermaid
flowchart LR
    A[Agent / orchestrator] -->|check: agent, task, tool, tokens| G

    subgraph G[Guard.check]
        direction TB
        I[identity.py<br/>SecOps: who, which tools]
        R[router.py<br/>FinOps: which tier, what cost]
        I --- R
    end

    G -->|Verdict| A
    G -->|every decision| L[(ledger.py<br/>audit.jsonl)]
    L --> D[dashboard.py<br/>one view, two audiences]
    L --> CLI[cli: report]
    A -->|if ALLOW: call model/tool| M[Model / Tool]
    M -->|real token usage| S[Guard.settle]
    S --> L
```

## Decision pipeline

Checks run in a fixed order: most security-critical and cheapest first. The first failure wins,
the call is **blocked (fail closed)**, and the attempt is still written to the audit log.

```mermaid
flowchart TD
    S([Call arrives]) --> Q1{Agent registered?}
    Q1 -- no --> B1[BLOCK_IDENTITY]
    Q1 -- yes --> Q2{Quarantined?}
    Q2 -- yes --> B2[BLOCK_QUARANTINE]
    Q2 -- no --> Q3{Tool in scope?}
    Q3 -- no --> B3[BLOCK_SCOPE<br/>violation logged in window<br/>quarantine at N in W seconds]
    Q3 -- yes --> Q4{Input within<br/>context cap?}
    Q4 -- no --> B4[BLOCK_CONTEXT]
    Q4 -- yes --> Q5{Under calls/min?}
    Q5 -- no --> B5[BLOCK_RATE]
    Q5 -- yes --> Q6{Projected spend<br/>within budget?}
    Q6 -- no --> B6[BLOCK_BUDGET]
    Q6 -- yes --> OK[ALLOW<br/>reserve cost,<br/>route to cheapest tier]

    classDef block fill:#fde8e8,stroke:#c0392b,color:#7b1d1d
    classDef ok fill:#e6f4ea,stroke:#2e7d32,color:#1b4d1f
    class B1,B2,B3,B4,B5,B6 block
    class OK ok
```

## Call lifecycle

```mermaid
sequenceDiagram
    participant Agent
    participant Guard
    participant Log as Audit log
    participant Model

    Agent->>Guard: check(agent, task, tool, est. tokens)
    Guard->>Guard: run pipeline (atomic under lock)
    Guard->>Log: decision event (allowed OR blocked)
    alt blocked
        Guard-->>Agent: Verdict(BLOCK_*, reason)
        Note over Agent: must not call model or tool
    else allowed
        Guard-->>Agent: Verdict(ALLOW, tier, call_id)
        Agent->>Model: call on routed tier
        Model-->>Agent: response + real token usage
        Agent->>Guard: settle(call_id, real tokens)
        Guard->>Log: settle event (estimate corrected)
    end
```

## Design decisions

| Decision | Why |
|---|---|
| **Fail closed.** Any non-`ALLOW` means do not proceed. | A guard that fails open is a suggestion. |
| **Log blocked calls, not just allowed ones.** | v0.1 only recorded allowed calls, so a blocked attack left the dashboard green. Blocked attempts *are* the security signal. |
| **Reserve at `check`, correct at `settle`.** | Estimates gate the call; real usage keeps the ledger honest. |
| **Atomic check-and-reserve under one lock.** | Without it, N concurrent calls can each pass the budget check and collectively overspend. |
| **Quarantine is automatic, release is manual.** | Repeated out-of-scope calls are an incident, not a retry loop. A human lifts it. |
| **Violations are counted in a sliding window, not a streak.** | A streak resets on every legal call, so alternating legal and illegal calls would never trip it (this was a real bug in 0.2.0). |
| **Money is `Decimal`, never `float`.** | Float sums drift (0.1 x 10 is not 1.0). A FinOps tool must be exact. |
| **`settle()` can only report an overrun, not prevent it.** | The call already happened. The guard raises `OVERRUN` and blocks the *next* call. |
| **Dashboard is computed from the audit log only.** | One source of truth. `report` on a log file gives the same answer as the live dashboard. |
| **Zero runtime dependencies.** | Drop-in anywhere; easy to audit a security tool. |

## Module map

| File | Responsibility |
|---|---|
| `guard.py` | The pipeline, `check()` and `settle()` |
| `identity.py` | Agent records, scopes, limits, thread-safe registry |
| `money.py` | Exact `Decimal` helpers |
| `router.py` | Task to tier mapping, cost math, routing-savings baseline |
| `ledger.py` | Append-only JSONL audit log |
| `dashboard.py` | `summarize()` and `render()` over audit events |
| `policy.py` | Load agents, prices, routes from JSON |
| `scenarios.py` / `cli.py` | Demo and `report` command |
