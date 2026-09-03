import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    token_type: str = "Bearer"
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token) and not self.is_expired


class BinanceTokenStore:
    def __init__(self) -> None:
        self._token: TokenData | None = None

    async def save(self, token: TokenData) -> None:
        self._token = token
        logger.info("Binance token saved (expires_at=%s)", token.expires_at)

    async def get(self) -> TokenData | None:
        if self._token and self._token.is_expired:
            logger.info("Cached token is expired")
            return None
        return self._token

    async def delete(self) -> None:
        self._token = None
        logger.info("Binance token deleted")

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None and self._token.is_valid


token_store = BinanceTokenStore()
