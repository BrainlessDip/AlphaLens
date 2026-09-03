from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


class BinanceAPIError(AppException):
    def __init__(self, message: str = "Binance API request failed") -> None:
        super().__init__(code="BINANCE_API_ERROR", message=message, status_code=502)


class AgentError(AppException):
    def __init__(self, message: str = "Agent processing failed") -> None:
        super().__init__(code="AGENT_ERROR", message=message, status_code=500)
