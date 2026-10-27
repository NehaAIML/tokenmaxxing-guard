# router.py
# Routes queries to the cheapest capable model.
# Mirrors EY's "invisible router" approach.

TASK_COMPLEXITY = {
    "refactor": "small",
    "summarize": "small",
    "classify": "small",
    "architecture": "frontier",
    "debug_complex": "frontier",
}

MODEL_COSTS = {
    "small":    {"input": 0.10, "output": 0.50},
    "frontier": {"input": 5.00, "output": 25.00},
}

def route(task_type: str) -> str:
    complexity = TASK_COMPLEXITY.get(task_type, "frontier")
    return complexity

def estimate_cost(task_type: str, input_tokens: int, output_tokens: int) -> float:
    tier = route(task_type)
    rates = MODEL_COSTS[tier]
    return (input_tokens / 1_000_000) * rates["input"] + \
           (output_tokens / 1_000_000) * rates["output"]
