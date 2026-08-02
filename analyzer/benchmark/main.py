"""Benchmark RSI divergence signals against forward price movement."""

from __future__ import annotations

import logging
import os
from typing import Any

import pandas as pd
from pandas import Timestamp

from analyzer.config import Config
from analyzer.fetchers.kucoin import KuCoinFetchError, fetch_klines
from analyzer.indicators.rsi import detect_rsi_divergences
from analyzer.indicators.sma import calculate_sma


DEFAULT_TICKERS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]


def _load_dotenv(path: str = ".env") -> None:
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("\"'")
                if key not in os.environ:
                    os.environ[key] = val
    except FileNotFoundError:
        pass


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


def main() -> None:
    _load_dotenv()
    cfg = Config()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("benchmark")

    logger.info(
        "benchmark started  days=%d  forward=%dd",
        cfg.benchmark_days,
        cfg.benchmark_forward_days,
    )
    logger.info(
        "rsi period=%d  order=%d  sma=%s",
        cfg.rsi_period,
        cfg.rsi_divergence_order,
        "on" if cfg.sma_enabled else "off",
    )

    for ticker in DEFAULT_TICKERS:
        logger.info("fetching %s klines...", ticker)
        try:
            df = fetch_klines(
                ticker,
                timeframe=cfg.kucoin_timeframe,
                base_url=cfg.kuCoin_base_url,
            )
        except KuCoinFetchError as e:
            logger.error("  skip %s - fetch error: %s", ticker, e)
            continue

        if len(df) < cfg.rsi_period + cfg.benchmark_forward_days + 1:
            logger.warning(
                "  skip %s - only %d candles", ticker, len(df)
            )
            continue

        signals, summary = run_benchmark(
            df,
            ticker=ticker,
            rsi_period=cfg.rsi_period,
            rsi_order=cfg.rsi_divergence_order,
            forward_days=cfg.benchmark_forward_days,
            sma_enabled=cfg.sma_enabled,
            sma_period=cfg.sma_period,
        )

        print_ledger(signals, summary, cfg.benchmark_forward_days)

    logger.info("done")


if __name__ == "__main__":
    main()
