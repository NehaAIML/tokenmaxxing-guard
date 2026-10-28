import json

from tokenmaxxing_guard import AuditLog, Guard, read_events
from tokenmaxxing_guard.cli import main
from tokenmaxxing_guard.dashboard import render, summarize


def test_attack_is_visible_on_dashboard(clock):
    """The headline regression: blocked attacks must change the dashboard status."""
    g = Guard(clock=clock)
    g.register("bot", ["read_file"], 5.0)
    for _ in range(12):
        g.check("bot", "debug_complex", "write_file", 40_000, 500)
    row = summarize(g.audit.events)["bot"]
    assert row["status"] == "QUARANTINED"
    assert row["blocked"] == 12 and row["avoided_usd"] > 0


def test_routing_savings_are_reported(clock):
    g = Guard(clock=clock)
    g.register("bot", ["read_file"], 5.0, max_input_tokens=2_000_000)
    g.check("bot", "summarize", "read_file", 1_000_000, 0)  # $0.10 small vs $5.00 frontier
    assert abs(summarize(g.audit.events)["bot"]["routing_savings_usd"] - 4.90) < 1e-6


def test_empty_dashboard():
    assert "No activity" in render({})


def test_audit_log_roundtrip_and_cli_report(tmp_path, clock, capsys):
    log = tmp_path / "audit.jsonl"
    g = Guard(audit=AuditLog(log), clock=clock)
    g.register("bot", ["read_file"], 5.0)
    g.check("bot", "summarize", "read_file", 100, 10)
    g.check("bot", "summarize", "write_file", 100, 10)
    assert len(read_events(log)) == 2

    assert main(["report", str(log), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["bot"]["allowed"] == 1 and data["bot"]["blocked"] == 1


def test_demo_command_runs(capsys):
    assert main(["demo"]) == 0
    assert "QUARANTINED" in capsys.readouterr().out
