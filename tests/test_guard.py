import threading
from decimal import Decimal

import pytest

from tokenmaxxing_guard import Decision, Guard


def violate(guard, n=1, tool="write_file"):
    return [guard.check("reader", "summarize", tool, 1, 1) for _ in range(n)][-1]


def test_allows_in_scope_call(guard):
    v = guard.check("reader", "summarize", "read_file", 1_000, 100)
    assert v.allowed and v.decision is Decision.ALLOW
    assert v.tier == "small" and v.call_id


def test_unknown_agent_is_blocked(guard):
    assert guard.check("ghost", "summarize", "read_file", 1, 1).decision is Decision.BLOCK_IDENTITY


def test_out_of_scope_tool_is_blocked(guard):
    assert violate(guard).decision is Decision.BLOCK_SCOPE


def test_blocked_attempts_are_recorded(guard):
    """Regression (v0.1): blocked calls were invisible and the dashboard showed OK."""
    violate(guard, 2)
    assert guard.registry.get("reader").blocked_calls == 2
    assert [e["decision"] for e in guard.audit.events] == ["BLOCK_SCOPE", "BLOCK_SCOPE"]


def test_repeated_violations_quarantine_the_agent(guard):
    violate(guard, 3)
    assert guard.registry.get("reader").quarantined
    v = guard.check("reader", "summarize", "read_file", 1, 1)
    assert v.decision is Decision.BLOCK_QUARANTINE  # even a legal call is refused


def test_alternating_legal_and_illegal_calls_still_quarantine(guard):
    """Regression (v0.2.0): a consecutive streak reset on every legal call, so alternating
    one legal + one illegal call was never quarantined. The window closes that evasion."""
    for _ in range(3):
        guard.check("reader", "summarize", "read_file", 1, 1)  # legal call "resets" nothing now
        guard.check("reader", "summarize", "write_file", 1, 1)
    assert guard.registry.get("reader").quarantined


def test_old_violations_age_out_of_the_window(guard, clock):
    violate(guard, 2)
    clock.advance(601)  # window is 600s
    violate(guard, 1)
    assert not guard.registry.get("reader").quarantined


def test_release_restores_access_and_clears_history(guard):
    violate(guard, 3)
    guard.registry.release("reader")
    assert guard.check("reader", "summarize", "read_file", 1, 1).allowed
    violate(guard, 2)  # history was cleared, so 2 is below the threshold of 3
    assert not guard.registry.get("reader").quarantined


def test_context_cap(guard):
    v = guard.check("reader", "summarize", "read_file", 10_001, 10)
    assert v.decision is Decision.BLOCK_CONTEXT


def test_rate_limit_and_window_expiry(guard, clock):
    for _ in range(5):
        assert guard.check("reader", "summarize", "read_file", 10, 10).allowed
    assert guard.check("reader", "summarize", "read_file", 10, 10).decision is Decision.BLOCK_RATE
    clock.advance(61)
    assert guard.check("reader", "summarize", "read_file", 10, 10).allowed


def test_budget_block_and_exact_budget_allowed(clock):
    g = Guard(clock=clock)
    g.register("p", ["search"], budget_usd="1.00")
    results = [g.check("p", "architecture", "search", 20_000, 4_000) for _ in range(6)]
    assert [r.allowed for r in results] == [True] * 5 + [False]
    assert results[-1].decision is Decision.BLOCK_BUDGET


def test_money_is_exact_not_floating_point(clock):
    """Three $0.10 calls must fit a $0.30 budget. With binary floats, a running total of
    0.1 + 0.1 + 0.1 is 0.30000000000000004, which exceeds 0.3 and wrongly blocks call 3."""
    g = Guard(clock=clock)
    g.register("p", ["t"], budget_usd="0.30", max_input_tokens=2_000_000)
    verdicts = [g.check("p", "summarize", "t", 1_000_000, 0) for _ in range(4)]  # $0.10 each
    assert [v.allowed for v in verdicts] == [True, True, True, False]
    assert g.registry.get("p").spent_usd == Decimal("0.30")


def test_budget_warning_alert_fires_once(clock):
    g = Guard(clock=clock)
    rec = g.register("p", ["search"], budget_usd="1.00")
    for _ in range(5):
        g.check("p", "architecture", "search", 20_000, 4_000)
    assert sum(a.startswith("BUDGET_WARNING") for a in rec.alerts) == 1


def test_settle_corrects_estimate(guard):
    v = guard.check("reader", "summarize", "read_file", 1_000, 1_000)
    before = guard.registry.get("reader").spent_usd
    delta = guard.settle(v.call_id, 500, 500)
    assert delta < 0
    assert guard.registry.get("reader").spent_usd == before + delta
    with pytest.raises(KeyError):
        guard.settle(v.call_id, 1, 1)  # already settled


def test_settle_raises_overrun_alert_when_real_usage_exceeds_budget(clock):
    g = Guard(clock=clock)
    rec = g.register("p", ["t"], budget_usd="0.20", max_input_tokens=2_000_000)
    v = g.check("p", "architecture", "t", 20_000, 4_000)  # estimate $0.20: exactly the budget
    assert v.allowed
    g.settle(v.call_id, 40_000, 8_000)  # reality: double the estimate -> $0.40
    assert rec.spent_usd == Decimal("0.4")
    assert any(a.startswith("OVERRUN") for a in rec.alerts)
    assert g.check("p", "architecture", "t", 1, 1).decision is Decision.BLOCK_BUDGET


def test_negative_tokens_rejected(guard):
    with pytest.raises(ValueError):
        guard.check("reader", "summarize", "read_file", -1, 0)


def test_concurrent_calls_cannot_overspend(clock):
    g = Guard(clock=clock)
    g.register("p", ["search"], budget_usd="1.00", max_calls_per_minute=10_000)
    verdicts = []

    def worker():
        for _ in range(20):
            verdicts.append(g.check("p", "architecture", "search", 20_000, 4_000))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(v.allowed for v in verdicts) == 5
    assert g.registry.get("p").spent_usd <= Decimal("1.00")
