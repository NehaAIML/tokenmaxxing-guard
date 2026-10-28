# Threat model

Scope: an autonomous agent that can call models and tools, run by an organisation that cares about
both its bill and its blast radius. This document states what the guard does and does not cover.

| # | Threat | Control | Decision code | Residual risk |
|---|---|---|---|---|
| T1 | Agent calls a tool outside its job (privilege creep, prompt-injected action) | Per-agent allow-list of tools | `BLOCK_SCOPE` | Allow-list is only as good as its author; scopes are per tool name, not per argument |
| T2 | Agent retries a denied action in a loop, or interleaves legal calls to hide it | Sliding-window violation count (N in W seconds), auto-quarantine, manual release | `BLOCK_QUARANTINE` | A very slow attacker staying under N violations per window; tune N and W per agent |
| T3 | Agent uses a shared or unknown identity | Unknown IDs are denied; no default or inherited identity | `BLOCK_IDENTITY` | The guard trusts the `agent_id` it is given; authenticating that ID is the caller's job (see Roadmap) |
| T4 | Context bloat ("tokenmaxxing"): huge prompts on every call | Per-call input cap | `BLOCK_CONTEXT` | Cap is a blunt instrument; legitimate large-context tasks need a higher-cap agent |
| T5 | Runaway loop on an *allowed* tool | Calls-per-minute window | `BLOCK_RATE` | Fixed-window logic can be gamed at window edges |
| T6 | Budget exhaustion | Reserve projected cost, hard stop at budget, 80% warning | `BLOCK_BUDGET` | Estimates can be wrong; `settle()` corrects them after the fact |
| T7 | Over-spend on easy tasks | Route cheap tasks to the small tier | n/a (FinOps) | Misclassified task types; unknown types default to the *capable* tier, not the cheap one |
| T8 | Concurrent calls overspend a budget | Atomic check-and-reserve under a lock | n/a | Single process only; not distributed (see Roadmap) |
| T9 | Attacker erases or corrupts evidence | Append-only JSONL, one `O_APPEND` write per event (no interleaved lines) | n/a | The file is only as tamper-proof as its storage; ship it to WORM/SIEM storage. Not safe on NFS |
| T10 | Spray of random agent IDs to bloat reports or logs | Unknown IDs pooled into one `<unregistered>` dashboard row | `BLOCK_IDENTITY` | The raw audit log still grows by one line per attempt; rate-limit upstream |
| T11 | Real usage far exceeds the estimate | `settle()` corrects spend and raises `OVERRUN` | n/a | Detection after the fact; one overrun call is already paid for |

## Explicitly out of scope

- Prompt-injection *detection* (this limits the damage, it does not detect the attack)
- Authentication of callers and secrets management
- Content filtering of prompts or responses
- Multi-process or multi-host state (state lives in one process today)
- Real provider billing reconciliation (prices are illustrative until you load your own)

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md).
