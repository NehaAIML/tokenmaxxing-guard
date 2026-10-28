import json
from decimal import Decimal

from tokenmaxxing_guard import AuditLog, Guard, read_events
from tokenmaxxing_guard.cli import main
from tokenmaxxing_guard.dashboard import render, summarize


def test_attack_is_visible_on_dashboard(clock):
    """The headline regression: blocked attacks must change the dashboard status."""
    g = Guard(clock=clock)
    g.register("bot", ["read_file"], "5.00")
    for _ in range(12):
        g.check("bot", "debug_complex", "write_file", 40_000, 500)
    row = summarize(g.audit.events)["bot"]
    assert row["status"] == "QUARANTINED"
    assert row["blocked"] == 12 and row["avoided_usd"] > 0


def test_routing_savings_are_reported(clock):
    g = Guard(clock=clock)
    g.register("bot", ["read_file"], "5.00", max_input_tokens=2_000_000)
    g.check("bot", "summarize", "read_file", 1_000_000, 0)  # $0.10 small vs $5.00 frontier
    assert summarize(g.audit.events)["bot"]["routing_savings_usd"] == Decimal("4.9")


def test_unregistered_ids_are_pooled_into_one_row(clock):
    g = Guard(clock=clock)
    for i in range(50):
        g.check(f"random-{i}", "summarize", "read_file", 10, 10)
    rows = summarize(g.audit.events)
    assert list(rows) == ["<unregistered>"]
    assert rows["<unregistered>"]["distinct_ids"] == 50
    assert "50 distinct IDs" in render(rows)


def test_overrun_status_after_settle(clock):
    g = Guard(clock=clock)
    g.register("p", ["t"], "0.20", max_input_tokens=2_000_000)
    v = g.check("p", "architecture", "t", 20_000, 4_000)
    g.settle(v.call_id, 40_000, 8_000)
    assert summarize(g.audit.events)["p"]["status"] == "BUDGET_EXCEEDED"


def test_warning_status_comes_from_the_guard_not_a_duplicate_threshold(clock):
    g = Guard(clock=clock, warn_ratio="0.5")
    g.register("p", ["t"], "1.00")
    for _ in range(3):  # $0.60 of $1.00 -> crosses 50%
        g.check("p", "architecture", "t", 20_000, 4_000)
    assert summarize(g.audit.events)["p"]["status"] == "BUDGET_WARNING"


def test_empty_dashboard():
    assert "No activity" in render({})


def test_audit_log_roundtrip_and_cli_report(tmp_path, clock, capsys):
    log = tmp_path / "audit.jsonl"
    g = Guard(audit=AuditLog(log), clock=clock)
    g.register("bot", ["read_file"], "5.00")
    g.check("bot", "summarize", "read_file", 100, 10)
    g.check("bot", "summarize", "write_file", 100, 10)
    assert len(read_events(log)) == 2

    assert main(["report", str(log), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["bot"]["allowed"] == 1 and data["bot"]["blocked"] == 1

    assert main(["report", str(log)]) == 0
    assert "TOKENMAXXING-GUARD" in capsys.readouterr().out


def test_demo_command_runs(capsys):
    assert main(["demo"]) == 0
    assert "QUARANTINED" in capsys.readouterr().out
