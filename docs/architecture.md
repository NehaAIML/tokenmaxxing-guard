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
