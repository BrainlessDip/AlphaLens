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
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    frontend_url: str = "http://localhost:5173"

    # JWT
    jwt_secret_key: str = "dev-secret-change-in-production-use-64-chars-minimum-for-sha256"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Token encryption key (Fernet). Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    token_encryption_key: str = ""

    # Binance OAuth (Client ID Metadata Document flow)
    binance_mcp_url: str = "https://agent.binance.com/mcp/agentic"
    binance_oauth_authorization_endpoint: str = "https://accounts.binance.com/agentic-oauth/authorize"
    binance_oauth_token_endpoint: str = "https://accounts.binance.com/oauth-agentic/token"
    binance_oauth_client_metadata_url: str = "http://127.0.0.1:8000/.well-known/oauth-client-metadata.json"
    binance_oauth_redirect_uri: str = "http://127.0.0.1:8000/api/v1/binance/auth/callback"
    binance_oauth_mcp_resource: str = "https://agent.binance.com/mcp/agentic"
    state_ttl_seconds: int = 600


@lru_cache
def get_settings() -> Settings:
    return Settings()
