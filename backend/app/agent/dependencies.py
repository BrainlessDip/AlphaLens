from dataclasses import dataclass

from app.binance.client import BinanceRESTProvider


@dataclass
class AgentDeps:
    provider: BinanceRESTProvider
