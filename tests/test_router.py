from decimal import Decimal

import pytest

from tokenmaxxing_guard import ModelTier, Router


def test_small_tasks_route_small():
    assert Router().route("summarize").name == "small"


def test_unknown_task_falls_back_to_default_tier():
    assert Router().route("never-heard-of-it").name == "frontier"


def test_cost_math_is_exact():
    # frontier: $5/M in, $25/M out -> 1M in + 1M out = $30 exactly
    assert Router().estimate_cost("architecture", 1_000_000, 1_000_000) == Decimal("30")


def test_tier_accepts_floats_but_stores_exact_decimals():
    tier = ModelTier("t", 0.1, 0.2)
    assert tier.input_per_mtok == Decimal("0.1") and tier.output_per_mtok == Decimal("0.2")


def test_baseline_is_most_expensive_tier():
    assert Router().baseline_cost(1_000_000, 0) == Decimal("5")


def test_routes_must_reference_defined_tiers():
    with pytest.raises(ValueError):
        Router(
            tiers={"small": ModelTier("small", 1, 1)}, routes={"x": "huge"}, default_tier="small"
        )
