from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Signal:
    ticker: str
    action: str
    confidence: float
    entry_price: float
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "reason": self.reason,
        }


@dataclass
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
