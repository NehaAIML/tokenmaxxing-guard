"""FinOps: send each task to the cheapest model tier that can handle it.

Prices below are ILLUSTRATIVE (USD per million tokens). Replace them with your
provider's current price list via a policy file before trusting any dollar figure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ModelTier:
    name: str
    input_per_mtok: float
    output_per_mtok: float

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1_000_000 * self.input_per_mtok
            + output_tokens / 1_000_000 * self.output_per_mtok
        )


DEFAULT_TIERS: Dict[str, ModelTier] = {
    "small": ModelTier("small", 0.10, 0.50),
    "frontier": ModelTier("frontier", 5.00, 25.00),
}

DEFAULT_ROUTES: Dict[str, str] = {
    "classify": "small",
    "summarize": "small",
    "refactor": "small",
    "architecture": "frontier",
    "debug_complex": "frontier",
}


class Router:
    def __init__(
        self,
        tiers: Optional[Dict[str, ModelTier]] = None,
        routes: Optional[Dict[str, str]] = None,
        default_tier: str = "frontier",
    ) -> None:
        self.tiers = dict(tiers or DEFAULT_TIERS)
        self.routes = dict(routes or DEFAULT_ROUTES)
        self.default_tier = default_tier
        unknown = ({default_tier} | set(self.routes.values())) - set(self.tiers)
        if unknown:
            raise ValueError(f"routes reference undefined tiers: {sorted(unknown)}")

    def route(self, task_type: str) -> ModelTier:
        """Unknown task types fall back to default_tier (fail-safe: capable, not cheap)."""
        return self.tiers[self.routes.get(task_type, self.default_tier)]

    def estimate_cost(self, task_type: str, input_tokens: int, output_tokens: int) -> float:
        return self.route(task_type).cost(input_tokens, output_tokens)

    def baseline_cost(self, input_tokens: int, output_tokens: int) -> float:
        """What this call would cost on the most expensive tier. Used to report routing savings."""
        return max(t.cost(input_tokens, output_tokens) for t in self.tiers.values())
