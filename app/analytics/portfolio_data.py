"""
Loads and validates portfolio + price data.

Today this just validates the incoming request payload. Swap `load_price_history`
to call a live market data API (IEX Cloud / Polygon.io / Alpha Vantage) instead of
trusting client-supplied history once you're past local development.
"""

from app.models.schemas import PortfolioRequest


def validate_portfolio(request: PortfolioRequest) -> None:
    tickers = {h.ticker for h in request.holdings}
    missing = tickers - set(request.price_history.keys())
    if missing:
        raise ValueError(f"Missing price history for tickers: {missing}")

    lengths = {len(v) for v in request.price_history.values()}
    if len(lengths) > 1:
        raise ValueError("All price history series must be the same length")
