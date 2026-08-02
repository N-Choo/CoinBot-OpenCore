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
