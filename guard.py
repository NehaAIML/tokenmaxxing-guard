# guard.py
# Wraps every agent call. Checks budget, identity, and behavior
# before the call reaches the model.

from router import route, estimate_cost
from identity import AGENT_REGISTRY, authorize, record_spend

def guarded_call(agent_id: str, task_type: str, tool: str,
                 input_tokens: int, output_tokens: int) -> dict:
    """
    Returns a decision: ALLOW, BLOCK_BUDGET, BLOCK_IDENTITY, ALERT_ANOMALY.
    This is the single control point where cost and security meet.
    """
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        return {"decision": "BLOCK_IDENTITY", "reason": "unknown_agent"}

    # SecOps check first: identity and permission
    if not authorize(agent_id, tool):
        return {"decision": "BLOCK_IDENTITY",
                "reason": f"tool '{tool}' not in allowed scope"}

    # FinOps check: budget
    projected = estimate_cost(task_type, input_tokens, output_tokens)
    if agent["spent_usd"] + projected > agent["budget_usd"]:
        return {"decision": "BLOCK_BUDGET",
                "reason": f"would exceed ${agent['budget_usd']}"}

    # Behavioral anomaly check: unusual call rate
    if agent["call_count"] > 50:
        agent["anomalies"].append("HIGH_CALL_RATE")
        return {"decision": "ALERT_ANOMALY",
                "reason": "call count exceeds baseline"}

    record_spend(agent_id, projected, tool)
    return {"decision": "ALLOW", "cost": projected,
            "tier": route(task_type)}
