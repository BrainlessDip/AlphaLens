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
    binance_mcp_url: str = "https://agent.binance.com/mcp/agentic"
    frontend_url: str = "http://localhost:5173"
    binance_oauth_authorization_endpoint: str = "https://accounts.binance.com/agentic-oauth/authorize"
    binance_oauth_token_endpoint: str = "https://accounts.binance.com/oauth-agentic/token"
    binance_oauth_client_id: str = ""
    binance_oauth_redirect_uri: str = "http://localhost:8000/api/v1/binance/auth/callback"
    binance_oauth_scopes: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
