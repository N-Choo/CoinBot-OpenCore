import pandas as pd
import numpy as np
from analyzer.indicators.rsi import calculate_rsi


def test_calculate_rsi_flat_series_returns_0():
    """Flat series has no gains, so RSI is 0 (division by epsilon yields 0 RS)."""
    close = pd.Series([100.0] * 20, name="Close")
    rsi = calculate_rsi(close, period=14)
    assert rsi.iloc[-1] == 0.0


def test_calculate_rsi_all_gains_returns_100():
    close = pd.Series(np.linspace(100, 200, 30), name="Close")
    rsi = calculate_rsi(close, period=14)
    assert rsi.iloc[-1] > 99.0


def test_calculate_rsi_known_oversold():
    np.random.seed(42)
    n = 100
    prices = [100.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + np.random.normal(-0.01, 0.02)))
    close = pd.Series(prices, name="Close")
    rsi = calculate_rsi(close, period=14)
    assert rsi.iloc[-1] < 50.0


def test_calculate_rsi_length_matches_input():
    close = pd.Series(np.random.randn(50).cumsum() + 100, name="Close")
    rsi = calculate_rsi(close, period=14)
    assert len(rsi) == len(close)
