import json
import threading

from tokenmaxxing_guard import AuditLog, read_events


def test_independent_writers_never_interleave_lines(tmp_path):
    """Separate AuditLog objects share no lock, like separate processes would not.
    O_APPEND + a single write per event must keep every line intact."""
    path = tmp_path / "audit.jsonl"
    padding = "x" * 2_000

    def writer(n):
        log = AuditLog(path)
        for i in range(100):
            log.record({"event": "decision", "writer": n, "i": i, "pad": padding})

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    lines = path.read_text().splitlines()
    assert len(lines) == 600
    assert all(json.loads(line)["pad"] == padding for line in lines)
    assert len(read_events(path)) == 600
