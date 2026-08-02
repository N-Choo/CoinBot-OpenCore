"""Benchmark RSI divergence signals against forward price movement."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas import Timestamp

from analyzer.indicators.rsi import detect_rsi_divergences
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


def run_benchmark(
    df: pd.DataFrame,
    ticker: str,
    rsi_period: int = 14,
    rsi_order: int = 5,
    forward_days: int = 7,
    sma_enabled: bool = False,
    sma_period: int = 20,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    eval_df = (
        df.iloc[: -forward_days] if len(df) > forward_days else df
    )
    result = detect_rsi_divergences(
        eval_df, rsi_period=rsi_period, order=rsi_order
    )

    signals: list[dict[str, Any]] = []
    buy_total = buy_hits = sell_total = sell_hits = 0

    for idx in range(len(result)):
        row_data = dict(result.iloc[idx])
        div_type = _make_divergence_label(row_data)
        if div_type == "unknown":
            continue

        action = "buy" if "bullish" in div_type else "sell"

        if sma_enabled:
            allowed = _apply_sma_filter(
                df["Close"], idx, action, sma_period
            )
            if not allowed:
                continue

        entry_price = float(df["Close"].iloc[idx])
        fwd_idx = idx + forward_days
        forward_price = (
            float(df["Close"].iloc[fwd_idx])
            if fwd_idx < len(df)
            else None
        )

        hit, pct = _score_signal(action, entry_price, forward_price)

        ts = df.index[idx]
        if isinstance(ts, Timestamp):
            date_str = ts.strftime("%Y-%m-%d")
        else:
            date_str = str(ts)

        signals.append({
            "ticker": ticker,
            "date": date_str,
            "action": action,
            "divergence": div_type,
            "entry_price": entry_price,
            "forward_price": forward_price,
            "pct": pct,
            "hit": hit,
        })

        if hit is not None:
            if action == "buy":
                buy_total += 1
                if hit:
                    buy_hits += 1
            else:
                sell_total += 1
                if hit:
                    sell_hits += 1

    return signals, {
        "ticker": ticker,
        "buy_hits": buy_hits,
        "buy_total": buy_total,
        "sell_hits": sell_hits,
        "sell_total": sell_total,
    }
