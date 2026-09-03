from pydantic import BaseModel


class TickerPrice(BaseModel):
    symbol: str
    price: float


class Ticker24h(BaseModel):
    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    prev_close_price: float
    last_price: float
    volume: float
    quote_volume: float
    high_price: float
    low_price: float
    open_price: float
    count: int


class Kline(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int


class OrderBookEntry(BaseModel):
    price: float
    quantity: float


class OrderBook(BaseModel):
    last_update_id: int
    bids: list[OrderBookEntry]
    asks: list[OrderBookEntry]
