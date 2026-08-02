import os
from unittest import mock
from analyzer.config import Config


def test_config_reads_env_with_defaults():
    with mock.patch.dict(os.environ, {}, clear=True):
        c = Config()
        assert c.redis_host == "localhost"
        assert c.redis_port == 6379
        assert c.redis_db == 0
        assert c.kuCoin_base_url == "https://api.kucoin.com"
        assert c.rsi_period == 14
        assert c.rsi_divergence_order == 5
        assert c.price_diff_threshold == 0.05
        assert c.result_channel == "signals:result"
        assert c.ticker_channel == "tickers:analyze"


def test_config_reads_custom_env():
    env = {
        "REDIS_HOST": "redis.local",
        "REDIS_PORT": "6380",
        "REDIS_DB": "1",
        "KUCOIN_BASE_URL": "https://api-futures.kucoin.com",
        "RSI_PERIOD": "10",
        "RSI_DIVERGENCE_ORDER": "7",
        "PRICE_DIFF_THRESHOLD": "0.08",
        "RESULT_CHANNEL": "signals:v1",
        "TICKER_CHANNEL": "tickers:v2",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        c = Config()
        assert c.redis_host == "redis.local"
        assert c.redis_port == 6380
        assert c.redis_db == 1
        assert c.kuCoin_base_url == "https://api-futures.kucoin.com"
        assert c.rsi_period == 10
        assert c.rsi_divergence_order == 7
        assert c.price_diff_threshold == 0.08
        assert c.result_channel == "signals:v1"
        assert c.ticker_channel == "tickers:v2"
