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


def print_ledger(
    signals: list[dict[str, Any]],
    summary: dict[str, Any],
    forward_days: int,
) -> None:
    ticker = summary["ticker"]
    W = "\u2550" * 67
    print()
    print(W)
    print(f"{ticker}  signals (forward {forward_days}d)")
    print("\u2500" * 67)

    if not signals:
        print("(no signals)")
        print(W)
        return

    print(
        f"{'date':<11} {'signal':<8} {'divergence':<20} "
        f"{'entry':>12} {str(forward_days) + 'd later':>12} "
        f"{'pct':>8}  hit"
    )
    for s in signals:
        mark = (
            "\u2713" if s["hit"] is True
            else ("\u2717" if s["hit"] is False else "-")
        )
        pct_str = (
            f"{s['pct']:+.1f}%" if s["pct"] is not None else "N/A"
        )
        entry_str = f"${s['entry_price']:,.0f}"
        fwd_str = (
            f"${s['forward_price']:,.0f}"
            if s["forward_price"] is not None
            else "N/A"
        )
        arrow = "\u25b2" if s["action"] == "buy" else "\u25bc"
        sig_label = f"{arrow} {s['action'].upper()}"
        print(
            f"{s['date']:<11} {sig_label:<8} "
            f"{s['divergence']:<20} {entry_str:>12} "
            f"{fwd_str:>12} {pct_str:>8}  {mark}"
        )

    print("\u2500" * 67)

    buy_pcts = [
        s["pct"] for s in signals
        if s["action"] == "buy" and s["pct"] is not None
    ]
    sell_pcts = [
        s["pct"] for s in signals
        if s["action"] == "sell" and s["pct"] is not None
    ]
    buy_avg = sum(buy_pcts) / len(buy_pcts) if buy_pcts else 0.0
    sell_avg = sum(sell_pcts) / len(sell_pcts) if sell_pcts else 0.0
    buy_rate = (
        f"buy  {summary['buy_hits']}/{summary['buy_total']}"
        f" ({summary['buy_hits'] / summary['buy_total'] * 100:.0f}%)"
        f" avg {buy_avg:+.1f}%"
        if summary["buy_total"] > 0
        else "buy  -"
    )
    sell_rate = (
        f"sell {summary['sell_hits']}/{summary['sell_total']}"
        f" ({summary['sell_hits'] / summary['sell_total'] * 100:.0f}%)"
        f" avg {sell_avg:+.1f}%"
        if summary["sell_total"] > 0
        else "sell -"
    )
    print(f"{buy_rate}  |  {sell_rate}")
    print(W)
