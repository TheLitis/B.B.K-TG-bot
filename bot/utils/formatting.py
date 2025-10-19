"""Utility helpers for formatting values and calculations."""

from __future__ import annotations

from math import ceil
from typing import Iterable


def calc_required(area_m2: float, waste_pct: int, pack_step: float | None) -> float:
    """Calculate total required material including waste and packaging constraints."""

    if area_m2 <= 0:
        return 0.0

    waste_multiplier = 1 + max(waste_pct, 0) / 100
    total = area_m2 * waste_multiplier

    if pack_step and pack_step > 0:
        packs = ceil(total / pack_step)
        return round(packs * pack_step, 2)

    return round(total, 2)


def bulletize(lines: Iterable[str]) -> str:
    """Join iterable lines into a human friendly bullet list."""

    filtered = [line.strip() for line in lines if line and line.strip()]
    return "\n".join(f"• {line}" for line in filtered)


__all__ = ["calc_required", "bulletize"]

