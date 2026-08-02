import numpy as np
from typing import Any

import pytest
from analyzer.benchmark.main import _score_signal


def test_score_buy_hit():
    hit, pct = _score_signal("buy", entry=100.0, forward=110.0)
    assert hit is True
    assert pct == pytest.approx(10.0)


def test_score_buy_miss():
    hit, pct = _score_signal("buy", entry=100.0, forward=95.0)
    assert hit is False
    assert pct == pytest.approx(-5.0)


def test_score_sell_hit():
    hit, pct = _score_signal("sell", entry=100.0, forward=90.0)
    assert hit is True
    assert pct == pytest.approx(-10.0)


def test_score_sell_miss():
    hit, pct = _score_signal("sell", entry=100.0, forward=105.0)
    assert hit is False
    assert pct == pytest.approx(5.0)


def test_score_na_when_no_forward():
    hit, pct = _score_signal("buy", entry=100.0, forward=None)
    assert hit is None
    assert pct is None


from analyzer.benchmark.main import _make_divergence_label


def test_divergence_label_regular_bullish():
    row_data = {"Reg_Bullish_Div": 1, "Reg_Bearish_Div": 0,
                "Hid_Bullish_Div": 0, "Hid_Bearish_Div": 0}
    assert _make_divergence_label(row_data) == "regular_bullish"


def test_divergence_label_regular_bearish():
    row_data = {"Reg_Bullish_Div": 0, "Reg_Bearish_Div": 1,
                "Hid_Bullish_Div": 0, "Hid_Bearish_Div": 0}
    assert _make_divergence_label(row_data) == "regular_bearish"


def test_divergence_label_hidden_bullish():
    row_data = {"Reg_Bullish_Div": 0, "Reg_Bearish_Div": 0,
                "Hid_Bullish_Div": 1, "Hid_Bearish_Div": 0}
    assert _make_divergence_label(row_data) == "hidden_bullish"


def test_divergence_label_hidden_bearish():
    row_data = {"Reg_Bullish_Div": 0, "Reg_Bearish_Div": 0,
                "Hid_Bullish_Div": 0, "Hid_Bearish_Div": 1}
    assert _make_divergence_label(row_data) == "hidden_bearish"


def test_divergence_label_no_match_returns_unknown():
    row_data = {"Reg_Bullish_Div": 0, "Reg_Bearish_Div": 0,
                "Hid_Bullish_Div": 0, "Hid_Bearish_Div": 0}
    assert _make_divergence_label(row_data) == "unknown"


import pandas as pd
from analyzer.benchmark.main import _apply_sma_filter


def test_sma_filter_allows_buy_above_sma():
    close = pd.Series([100.0] * 20 + [110.0])
    assert _apply_sma_filter(close, idx=20, action="buy", sma_period=5) is True


def test_sma_filter_blocks_buy_below_sma():
    close = pd.Series([100.0] * 20 + [90.0])
    assert _apply_sma_filter(close, idx=20, action="buy", sma_period=5) is False


def test_sma_filter_allows_sell_below_sma():
    close = pd.Series([100.0] * 20 + [90.0])
    assert _apply_sma_filter(close, idx=20, action="sell", sma_period=5) is True


def test_sma_filter_blocks_sell_above_sma():
    close = pd.Series([100.0] * 20 + [110.0])
    assert _apply_sma_filter(close, idx=20, action="sell", sma_period=5) is False


def test_sma_filter_short_window_returns_true():
    close = pd.Series([100.0] * 3)
    assert _apply_sma_filter(close, idx=2, action="buy", sma_period=5) is True


from analyzer.benchmark.main import run_benchmark


def test_run_benchmark_on_synthetic_data():
    """End-to-end: inject a known bullish divergence and verify it scores a buy hit."""
    rng = np.random.RandomState(42)
    n = 130
    noise = rng.randn(n) * 0.15

    close = np.zeros(n)
    for i in range(n):
        if i < 55:
            close[i] = 100 - i * 0.5 + noise[i]
        elif i < 60:
            close[i] = close[i - 1] + 0.5 + noise[i]
        elif i < 85:
            close[i] = close[i - 1] - 0.3 + noise[i]
        elif i < 97:
            close[i] = close[i - 1] - 0.05 + noise[i]
        else:
            close[i] = close[i - 1] + 0.6 + noise[i]

    high = close + 0.8
    low = close - 0.8
    low[96] = low[95] - 3.0

    df = pd.DataFrame({"High": high, "Low": low, "Close": close})

    signals, summary = run_benchmark(
        df,
        ticker="TEST-USDT",
        rsi_period=14,
        rsi_order=10,
        forward_days=7,
        sma_enabled=False,
        sma_period=20,
    )

    buy_signals = [s for s in signals if s["action"] == "buy"]
    assert len(buy_signals) >= 1

    buy_hits = [s for s in buy_signals if s["hit"] is True]
    assert len(buy_hits) >= 1

    assert summary["buy_total"] >= 1
    assert summary["buy_hits"] >= 1
