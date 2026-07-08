from pydantic import BaseModel, Field


class Holding(BaseModel):
    ticker: str
    sector: str
    shares: float
    price: float
    beta: float = Field(1.0, description="Beta vs. benchmark (e.g. S&P 500)")


class PortfolioRequest(BaseModel):
    portfolio_id: str
    benchmark_ticker: str = "SPY"
    holdings: list[Holding]
    # price_history: {ticker: [daily_returns]} — simplified daily return series per holding
    price_history: dict[str, list[float]]
    benchmark_history: list[float]
    confidence_level: float = 0.95
    risk_free_rate: float = 0.04


class RiskMetrics(BaseModel):
    portfolio_value: float
    value_at_risk_95: float
    value_at_risk_pct: float
    sharpe_ratio: float
    beta_weighted_exposure: float
    sector_concentration: dict[str, float]
    correlation_matrix: dict[str, dict[str, float]]


class PortfolioSummaryResponse(BaseModel):
    portfolio_id: str
    metrics: RiskMetrics
    summary: str
    cached: bool = False
