import os


class Config:
    def __init__(self) -> None:
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.kuCoin_base_url = os.getenv(
            "KUCOIN_BASE_URL", "https://api.kucoin.com"
        )
        self.kucoin_timeframe = os.getenv(
            "KUCOIN_TIMEFRAME", "1day"
        )
        self.rsi_period = int(os.getenv("RSI_PERIOD", "14"))
        self.rsi_divergence_order = int(
            os.getenv("RSI_DIVERGENCE_ORDER", "5")
        )
        self.price_diff_threshold = float(
            os.getenv("PRICE_DIFF_THRESHOLD", "0.05")
        )
        self.sma_enabled = os.getenv("SMA_ENABLED", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        self.sma_period = int(os.getenv("SMA_PERIOD", "20"))
        self.benchmark_days = int(os.getenv("BENCHMARK_DAYS", "90"))
        self.benchmark_forward_days = int(
            os.getenv("BENCHMARK_FORWARD_DAYS", "7")
        )
        self.result_channel = os.getenv(
            "RESULT_CHANNEL", "signals:result"
        )
        self.ticker_channel = os.getenv(
            "TICKER_CHANNEL", "tickers:analyze"
        )
