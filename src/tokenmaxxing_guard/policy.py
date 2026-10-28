"""Load agents, model prices and routes from a JSON policy file (no third-party deps)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Union

from .identity import AgentRegistry
from .money import to_decimal
from .router import ModelTier, Router


def load_policy(path: Union[str, Path]) -> Tuple[AgentRegistry, Router]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})

    tiers = {
        name: ModelTier(
            name, to_decimal(spec["input_per_mtok"]), to_decimal(spec["output_per_mtok"])
        )
        for name, spec in data.get("models", {}).items()
    } or None
    router = Router(
        tiers=tiers,
        routes=data.get("routes") or None,
        default_tier=data.get("default_tier", "frontier"),
    )

    registry = AgentRegistry()
    for agent_id, spec in data.get("agents", {}).items():
        merged = {**defaults, **spec}
        registry.register(
            agent_id,
            merged["allowed_tools"],
            merged["budget_usd"],
            max_input_tokens=merged.get("max_input_tokens", 32_000),
            max_calls_per_minute=merged.get("max_calls_per_minute", 60),
            quarantine_after_denials=merged.get("quarantine_after_denials", 5),
            quarantine_window_seconds=merged.get("quarantine_window_seconds", 600),
        )
    return registry, router
