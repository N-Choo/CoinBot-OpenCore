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


def _make_divergence_label(row_data: dict) -> str:
    if row_data.get("Reg_Bullish_Div"):
        return "regular_bullish"
    if row_data.get("Reg_Bearish_Div"):
        return "regular_bearish"
    if row_data.get("Hid_Bullish_Div"):
        return "hidden_bullish"
    if row_data.get("Hid_Bearish_Div"):
        return "hidden_bearish"
    return "unknown"
