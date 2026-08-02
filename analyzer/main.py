import json
import logging
import os
import time

import redis


def _load_dotenv(path: str = ".env") -> None:
    """Load key=value pairs from a .env file into os.environ."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("\"'")
                if key not in os.environ:
                    os.environ[key] = val
    except FileNotFoundError:
        pass


_load_dotenv()

from analyzer.config import Config
from analyzer.fetchers.kucoin import KuCoinFetchError, fetch_klines
from analyzer.indicators.rsi import calculate_rsi
from analyzer.publisher.redis_pub import publish_signals
from analyzer.signals.generator import generate_signals

logger = logging.getLogger(__name__)

BAR = "─" * 60


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )


def analyze_ticker(ticker: str, cfg: Config, redis_client: redis.Redis) -> None:
    t0 = time.monotonic()

    try:
        symbol = ticker.replace("/", "-")
        df = fetch_klines(symbol, timeframe=cfg.kucoin_timeframe, base_url=cfg.kuCoin_base_url)
    except KuCoinFetchError as e:
        logger.error("  ✗ %-12s  fetch failed — %s", ticker, e)
        return
    except Exception as e:
        logger.error("  ✗ %-12s  unexpected error — %s", ticker, e)
        return

    if len(df) < cfg.rsi_period + 1:
        logger.warning(
            "  ✗ %-12s  only %d candles (need >%d)",
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
        sma_enabled=cfg.sma_enabled,
        sma_period=cfg.sma_period,
    )

    t1 = time.monotonic()
    elapsed = (t1 - t0) * 1000

    latest_close = df["Close"].iloc[-1]
    latest_rsi = calculate_rsi(df["Close"], period=cfg.rsi_period).iloc[-1]

    buy_n = sum(1 for s in signals if s.action == "buy")
    sell_n = sum(1 for s in signals if s.action == "sell")

    if signals:
        logger.info(
            "  ✓ %-12s  price=%-12s  rsi=%-5.1f  "
            "candles=%-4d  buy=%-2d  sell=%-2d  %dms",
            ticker,
            f"${latest_close:,.2f}",
            latest_rsi,
            len(df),
            buy_n,
            sell_n,
            round(elapsed),
        )
        for s in signals:
            arrow = "▲" if s.action == "buy" else "▼"
            logger.info(
                "    %s  %-4s  conf=%.1f  @$%.2f  %s",
                arrow,
                s.action.upper(),
                s.confidence,
                s.entry_price,
                s.reason,
            )
    else:
        logger.info(
            "  ✓ %-12s  price=%-12s  rsi=%-5.1f  candles=%-4d  no signals  %dms",
            ticker,
            f"${latest_close:,.2f}",
            latest_rsi,
            len(df),
            round(elapsed),
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

    logger.info("")
    logger.info(BAR)
    logger.info("  analyzer started")
    logger.info(
        "  redis    %s:%d  (channel: %s)",
        cfg.redis_host,
        cfg.redis_port,
        cfg.ticker_channel,
    )
    logger.info("  kuCoin   %s  (timeframe: %s)",
                 cfg.kuCoin_base_url, cfg.kucoin_timeframe)
    logger.info(
        "  rsi      period=%d  order=%d",
        cfg.rsi_period,
        cfg.rsi_divergence_order,
    )
    logger.info(
        "  sma      enabled=%s  period=%d",
        "yes" if cfg.sma_enabled else "no",
        cfg.sma_period,
    )
    logger.info(BAR)
    logger.info("")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            tickers = json.loads(message["data"])
        except json.JSONDecodeError:
            logger.warning("invalid JSON on %s", cfg.ticker_channel)
            continue

        batch_id = time.strftime("%H:%M:%S")
        logger.info("%s  batch %s  (%d tickers)", BAR, batch_id, len(tickers))

        for ticker in tickers:
            time.sleep(0.1)
            analyze_ticker(ticker, cfg, r)

        logger.info("")


if __name__ == "__main__":
    main()
