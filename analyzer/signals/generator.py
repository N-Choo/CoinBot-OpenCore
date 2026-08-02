import pandas as pd

from analyzer.indicators.rsi import detect_rsi_divergences
from analyzer.models.types import Signal


def _compute_price_diff(df: pd.DataFrame, lookback: int = 7) -> float:
    """Weekly price change as a fraction."""
    if len(df) < lookback:
        return 0.0
    recent = df["Close"].iloc[-1]
    past = df["Close"].iloc[-lookback]
    return (recent - past) / past if past != 0 else 0.0


def generate_signals(
    df: pd.DataFrame,
    ticker: str,
    rsi_period: int = 14,
    rsi_order: int = 5,
    price_diff_threshold: float = 0.05,
) -> list[Signal]:
    """Generate ONE trading signal from the most recent RSI divergence.

    Scans divergence results backwards and returns only the latest
    actionable signal. Regular divergences take priority over hidden.
    """
    result = detect_rsi_divergences(df, rsi_period=rsi_period, order=rsi_order)

    price_diff = _compute_price_diff(df)
    latest_close = df["Close"].iloc[-1]
    latest_rsi = result["RSI"].iloc[-1]

    # pick the single most recent divergence, scanning from newest → oldest
    reg_bull = 0
    hid_bull = 0
    reg_bear = 0
    hid_bear = 0

    for idx in range(len(result) - 1, -1, -1):
        row = result.iloc[idx]
        if reg_bull == 0 and row["Reg_Bullish_Div"] == 1:
            reg_bull = idx
        if hid_bull == 0 and row["Hid_Bullish_Div"] == 1:
            hid_bull = idx
        if reg_bear == 0 and row["Reg_Bearish_Div"] == 1:
            reg_bear = idx
        if hid_bear == 0 and row["Hid_Bearish_Div"] == 1:
            hid_bear = idx

        if reg_bull and reg_bear and hid_bull and hid_bear:
            break

    candidates: list[tuple[int, str, str, float]] = []

    if reg_bull:
        c = 0.8 if latest_rsi < 30 else 0.6
        if price_diff < -price_diff_threshold:
            c = min(c + 0.1, 1.0)
        candidates.append((reg_bull, "buy", "regular_bullish_divergence", c))
    if reg_bear:
        c = 0.8 if latest_rsi > 70 else 0.6
        if price_diff > price_diff_threshold:
            c = min(c + 0.1, 1.0)
        candidates.append((reg_bear, "sell", "regular_bearish_divergence", c))
    if hid_bull:
        c = 0.5
        if price_diff < -price_diff_threshold:
            c = min(c + 0.1, 1.0)
        candidates.append((hid_bull, "buy", "hidden_bullish_divergence", c))
    if hid_bear:
        c = 0.5
        if price_diff > price_diff_threshold:
            c = min(c + 0.1, 1.0)
        candidates.append((hid_bear, "sell", "hidden_bearish_divergence", c))

    if not candidates:
        return []

    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0]

    return [
        Signal(
            ticker=ticker,
            action=best[1],
            confidence=best[3],
            entry_price=latest_close,
            reason=best[2],
        )
    ]
