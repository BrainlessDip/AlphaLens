from dataclasses import dataclass, field

from app.binance.client import BinanceRESTProvider
from app.binance.sub_account_service import SubAccountService


@dataclass
class AgentDeps:
    provider: BinanceRESTProvider
    sub_account: SubAccountService | None = None
