import json

import pytest

from tokenmaxxing_guard import AgentRegistry, Guard


def test_duplicate_registration_rejected():
    r = AgentRegistry()
    r.register("a", ["t"], 1.0)
    with pytest.raises(ValueError):
        r.register("a", ["t"], 1.0)


@pytest.mark.parametrize(
    "bad", [dict(agent_id=" ", budget_usd=1), dict(agent_id="a", budget_usd=-1)]
)
def test_invalid_registration(bad):
    with pytest.raises(ValueError):
        AgentRegistry().register(bad["agent_id"], ["t"], bad["budget_usd"])


def test_policy_file_roundtrip(tmp_path):
    policy = {
        "defaults": {"max_calls_per_minute": 7, "max_input_tokens": 2_000_000},
        "models": {"cheap": {"input_per_mtok": 1, "output_per_mtok": 2}},
        "routes": {"summarize": "cheap"},
        "default_tier": "cheap",
        "agents": {"bot": {"allowed_tools": ["read_file"], "budget_usd": 3.5}},
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    g = Guard.from_policy(path)
    rec = g.registry.get("bot")
    assert rec.budget_usd == 3.5 and rec.max_calls_per_minute == 7
    assert g.check("bot", "summarize", "read_file", 1_000_000, 0).cost_usd == pytest.approx(1.0)
