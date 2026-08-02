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
    """Generate trading signals from RSI divergences + price momentum.

    Returns only actionable signals (buy/sell). Holds are not emitted.
    """
    result = detect_rsi_divergences(df, rsi_period=rsi_period, order=rsi_order)
    signals: list[Signal] = []

    price_diff = _compute_price_diff(df)
    latest_close = df["Close"].iloc[-1]
    latest_rsi = result["RSI"].iloc[-1]

    for idx in range(len(result)):
        row = result.iloc[idx]
        if row["Reg_Bullish_Div"] == 1:
            confidence = 0.8 if latest_rsi < 30 else 0.6
            if price_diff < -price_diff_threshold:
                confidence = min(confidence + 0.1, 1.0)
            signals.append(
                Signal(
                    ticker=ticker,
                    action="buy",
                    confidence=confidence,
                    entry_price=latest_close,
                    reason="regular_bullish_divergence",
                )
            )
        elif row["Hid_Bullish_Div"] == 1:
            confidence = 0.5
            if price_diff < -price_diff_threshold:
                confidence = min(confidence + 0.1, 1.0)
            signals.append(
                Signal(
                    ticker=ticker,
                    action="buy",
                    confidence=confidence,
                    entry_price=latest_close,
                    reason="hidden_bullish_divergence",
                )
            )
        elif row["Reg_Bearish_Div"] == 1:
            confidence = 0.8 if latest_rsi > 70 else 0.6
            if price_diff > price_diff_threshold:
                confidence = min(confidence + 0.1, 1.0)
            signals.append(
                Signal(
                    ticker=ticker,
                    action="sell",
                    confidence=confidence,
                    entry_price=latest_close,
                    reason="regular_bearish_divergence",
                )
            )
        elif row["Hid_Bearish_Div"] == 1:
            confidence = 0.5
            if price_diff > price_diff_threshold:
                confidence = min(confidence + 0.1, 1.0)
            signals.append(
                Signal(
                    ticker=ticker,
                    action="sell",
                    confidence=confidence,
                    entry_price=latest_close,
                    reason="hidden_bearish_divergence",
                )
            )

    return signals
