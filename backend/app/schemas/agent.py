from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096, description="Natural language market question")


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading pair symbol, e.g. BTCUSDT")
    question: str = Field(..., min_length=1, max_length=2048, description="Market analysis question")


class PriceInfo(BaseModel):
    symbol: str
    price: float
    change_pct: float | None = None


class VolumeInfo(BaseModel):
    volume_24h: float
    quote_volume_24h: float


class AnalyzeResponse(BaseModel):
    symbol: str
    current_price: float
    price_change: PriceInfo
    volume_info: VolumeInfo
    market_observations: list[str]
    agent_analysis: str
    confidence_and_limitations: str
