"""Benchmark RSI divergence signals against forward price movement."""

from __future__ import annotations

import pandas as pd

from analyzer.indicators.sma import calculate_sma


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


def _apply_sma_filter(
    close_series: pd.Series,
    idx: int,
    action: str,
    sma_period: int,
) -> bool:
    window = close_series.iloc[: idx + 1]
    if len(window) < sma_period:
        return True
    sma_val = calculate_sma(window, period=sma_period).iloc[-1]
    price = float(close_series.iloc[idx])
    if action == "buy":
        return bool(price > sma_val)
    return bool(price < sma_val)
