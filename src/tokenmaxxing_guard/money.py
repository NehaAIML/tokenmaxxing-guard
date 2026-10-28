"""Exact money arithmetic. Binary floats are the wrong type for a FinOps tool."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Union

Number = Union[int, float, str, Decimal]

ZERO = Decimal("0")
MILLION = Decimal(1_000_000)
_SIX_PLACES = Decimal("0.000001")


def to_decimal(value: Number) -> Decimal:
    """Convert via ``str`` so ``0.1`` means exactly 0.1, not 0.1000000000000000055."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"not a valid number: {value!r}") from exc


def quantize(value: Decimal) -> Decimal:
    """Round to micro-dollars for storage and display."""
    return value.quantize(_SIX_PLACES, rounding=ROUND_HALF_UP)
