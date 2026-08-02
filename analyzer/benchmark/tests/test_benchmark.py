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
