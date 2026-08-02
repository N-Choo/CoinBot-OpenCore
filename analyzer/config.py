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
        self.result_channel = os.getenv(
            "RESULT_CHANNEL", "signals:result"
        )
        self.ticker_channel = os.getenv(
            "TICKER_CHANNEL", "tickers:analyze"
        )
