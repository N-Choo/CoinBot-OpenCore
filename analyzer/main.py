import json
import logging
import time

import redis

from analyzer.config import Config
from analyzer.fetchers.kucoin import fetch_klines, KuCoinFetchError
from analyzer.models.types import Signal
from analyzer.publisher.redis_pub import publish_signals
from analyzer.signals.generator import generate_signals

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def analyze_ticker(
    ticker: str, cfg: Config, redis_client: redis.Redis
) -> None:
    """Fetch OHLCV, compute signals, and publish results for a ticker."""
    try:
        symbol = ticker.replace("/", "-")
        df = fetch_klines(symbol, base_url=cfg.kuCoin_base_url)
    except KuCoinFetchError as e:
        logger.warning("Skipping %s — fetch failed: %s", ticker, e)
        return
    except Exception as e:
        logger.warning("Skipping %s — unexpected error: %s", ticker, e)
        return

    if len(df) < cfg.rsi_period + 1:
        logger.info(
            "Skipping %s — only %d data points (need >%d)",
            ticker,
            len(df),
            cfg.rsi_period,
        )
        return

    signals = generate_signals(
        df,
        ticker=ticker,
        rsi_period=cfg.rsi_period,
        rsi_order=cfg.rsi_divergence_order,
        price_diff_threshold=cfg.price_diff_threshold,
    )

    publish_signals(redis_client, signals, channel=cfg.result_channel)


def main() -> None:
    configure_logging()
    cfg = Config()

    r = redis.Redis(
        host=cfg.redis_host,
        port=cfg.redis_port,
        db=cfg.redis_db,
        decode_responses=True,
    )
    pubsub = r.pubsub()
    pubsub.subscribe(cfg.ticker_channel)
    logger.info("Listening on channel '%s'...", cfg.ticker_channel)

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            tickers = json.loads(message["data"])
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON on %s", cfg.ticker_channel)
            continue

        logger.info("Received %d ticker(s): %s", len(tickers), tickers)

        for ticker in tickers:
            time.sleep(0.1)
            analyze_ticker(ticker, cfg, r)


if __name__ == "__main__":
    main()
