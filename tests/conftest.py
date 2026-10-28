import pytest

from tokenmaxxing_guard import Guard


class FakeClock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def guard(clock):
    g = Guard(clock=clock)
    g.register(
        "reader",
        ["read_file"],
        budget_usd=1.00,
        max_input_tokens=10_000,
        max_calls_per_minute=5,
        quarantine_after_denials=3,
    )
    return g
