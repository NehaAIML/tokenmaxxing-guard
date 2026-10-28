import threading

import pytest

from tokenmaxxing_guard import Decision, Guard


def test_allows_in_scope_call(guard):
    v = guard.check("reader", "summarize", "read_file", 1_000, 100)
    assert v.allowed and v.decision is Decision.ALLOW
    assert v.tier == "small" and v.call_id


def test_unknown_agent_is_blocked(guard):
    v = guard.check("ghost", "summarize", "read_file", 1, 1)
    assert v.decision is Decision.BLOCK_IDENTITY


def test_out_of_scope_tool_is_blocked(guard):
    v = guard.check("reader", "summarize", "write_file", 1, 1)
    assert v.decision is Decision.BLOCK_SCOPE


def test_blocked_attempts_are_recorded(guard):
    """Regression: the v0.1 demo recorded nothing for blocked calls and showed status OK."""
    for _ in range(2):
        guard.check("reader", "summarize", "write_file", 1_000, 10)
    assert guard.registry.get("reader").blocked_calls == 2
    assert [e["decision"] for e in guard.audit.events] == ["BLOCK_SCOPE", "BLOCK_SCOPE"]


def test_repeated_violations_quarantine_the_agent(guard):
    for _ in range(3):
        guard.check("reader", "summarize", "write_file", 1, 1)
    assert guard.registry.get("reader").quarantined
    # even a perfectly legal call is refused while quarantined
    v = guard.check("reader", "summarize", "read_file", 1, 1)
    assert v.decision is Decision.BLOCK_QUARANTINE


def test_release_restores_access(guard):
    for _ in range(3):
        guard.check("reader", "summarize", "write_file", 1, 1)
    guard.registry.release("reader")
    assert guard.check("reader", "summarize", "read_file", 1, 1).allowed


def test_legal_call_resets_violation_streak(guard):
    guard.check("reader", "summarize", "write_file", 1, 1)
    guard.check("reader", "summarize", "write_file", 1, 1)
    guard.check("reader", "summarize", "read_file", 1, 1)
    guard.check("reader", "summarize", "write_file", 1, 1)
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
    g.register("p", ["search"], budget_usd=1.00)
    # architecture / frontier: 20k in + 4k out = $0.20 per call
    results = [g.check("p", "architecture", "search", 20_000, 4_000) for _ in range(6)]
    assert [r.allowed for r in results] == [True] * 5 + [False]
    assert results[-1].decision is Decision.BLOCK_BUDGET


def test_budget_warning_alert_fires_once(clock):
    g = Guard(clock=clock)
    rec = g.register("p", ["search"], budget_usd=1.00)
    for _ in range(5):
        g.check("p", "architecture", "search", 20_000, 4_000)
    assert sum(a.startswith("BUDGET_WARNING") for a in rec.alerts) == 1


def test_settle_corrects_estimate(guard):
    v = guard.check("reader", "summarize", "read_file", 1_000, 1_000)
    before = guard.registry.get("reader").spent_usd
    delta = guard.settle(v.call_id, 500, 500)
    assert delta < 0
    assert guard.registry.get("reader").spent_usd == pytest.approx(before + delta)
    with pytest.raises(KeyError):
        guard.settle(v.call_id, 1, 1)  # already settled


def test_negative_tokens_rejected(guard):
    with pytest.raises(ValueError):
        guard.check("reader", "summarize", "read_file", -1, 0)


def test_concurrent_calls_cannot_overspend(clock):
    g = Guard(clock=clock)
    g.register("p", ["search"], budget_usd=1.00, max_calls_per_minute=10_000)
    verdicts = []

    def worker():
        for _ in range(20):
            verdicts.append(g.check("p", "architecture", "search", 20_000, 4_000))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sum(v.allowed for v in verdicts) == 5
    assert g.registry.get("p").spent_usd <= 1.00 + 1e-9
