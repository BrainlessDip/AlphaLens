"""Legacy TokenData model. Token storage is now database-backed via BinanceOAuthConnection."""
import time
from dataclasses import dataclass


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
