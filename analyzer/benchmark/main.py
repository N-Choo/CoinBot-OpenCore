"""Benchmark RSI divergence signals against forward price movement."""

from __future__ import annotations


def _score_signal(
    action: str, entry: float, forward: float | None
) -> tuple[bool | None, float | None]:
    if forward is None:
        return None, None
    pct = ((forward - entry) / entry) * 100
    if action == "buy":
        return pct > 0, pct
    return pct < 0, pct
