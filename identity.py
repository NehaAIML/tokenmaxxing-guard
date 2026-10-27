# identity.py
# Every agent gets a unique identity and a scoped permission set.
# No shared service accounts. No inherited admin rights.

AGENT_REGISTRY = {}

def register_agent(agent_id: str, allowed_tools: list, budget_usd: float):
    """Assign a unique identity with explicit scope."""
    if agent_id in AGENT_REGISTRY:
        raise ValueError(f"Agent {agent_id} already registered")
    AGENT_REGISTRY[agent_id] = {
        "agent_id": agent_id,
        "allowed_tools": set(allowed_tools),
        "budget_usd": budget_usd,
        "spent_usd": 0.0,
        "call_count": 0,
        "anomalies": [],
    }

def authorize(agent_id: str, tool: str) -> bool:
    """Least-privilege check before any tool call."""
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        raise PermissionError(f"Unknown agent: {agent_id}")
    return tool in agent["allowed_tools"]

def record_spend(agent_id: str, cost: float, tool: str):
    """Track spend and baseline behavior."""
    agent = AGENT_REGISTRY[agent_id]
    agent["spent_usd"] += cost
    agent["call_count"] += 1
    if agent["spent_usd"] > agent["budget_usd"]:
        agent["anomalies"].append(f"BUDGET_EXCEEDED: ${agent['spent_usd']:.2f}")
    if tool not in agent["allowed_tools"]:
        agent["anomalies"].append(f"UNAUTHORIZED_TOOL: {tool}")
