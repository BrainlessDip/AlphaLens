from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    frontend_url: str = "http://localhost:5173"

    # OpenRouter (LLM provider, backend-only)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_app_url: str = ""
    openrouter_app_title: str = ""

    # JWT
    jwt_secret_key: str = (
        "dev-secret-change-in-production-use-64-chars-minimum-for-sha256"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Binance REST API (public market data needs no auth)
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_base_url: str = "https://api.binance.com"
    binance_request_timeout: float = 10.0

    # Binance Sub-Account API (requires master account API key with sub-account permissions)
    binance_sub_account_api_key: str = ""
    binance_sub_account_api_secret: str = ""

    # Binance Testnet/Sandbox mode
    binance_testnet: bool = False

    @property
    def binance_is_testnet(self) -> bool:
        """True when running in testnet/sandbox mode.

        Auto-enables testnet when no production credentials are configured.
        Explicit BINANCE_TESTNET=true always forces testnet.
        """
        if self.binance_testnet:
            return True
        # Auto-enable testnet when no credentials configured
        if not self.binance_api_key or not self.binance_api_secret:
            return True
        return False

    @property
    def binance_effective_base_url(self) -> str:
        """Resolved base URL: testnet endpoint or production."""
        if self.binance_is_testnet:
            return "https://testnet.binance.vision"
        return self.binance_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
