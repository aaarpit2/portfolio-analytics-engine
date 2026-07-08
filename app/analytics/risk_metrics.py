"""
Structured analytics layer.

Everything in here is deterministic, testable math — pandas/NumPy only.
No LLM calls happen here. This module's output is what gets injected
into the LLM prompt later, so the narrative is always grounded in real numbers.
"""

import numpy as np
import pandas as pd

from app.models.schemas import Holding, RiskMetrics


def _portfolio_weights(holdings: list[Holding]) -> pd.Series:
    values = pd.Series({h.ticker: h.shares * h.price for h in holdings})
    return values / values.sum()


def portfolio_value(holdings: list[Holding]) -> float:
    return float(sum(h.shares * h.price for h in holdings))


def value_at_risk(
    holdings: list[Holding],
    price_history: dict[str, list[float]],
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """
    Historical-simulation VaR: apply each historical daily return day to the
    current portfolio weights, then take the loss at the given percentile.
    Returns (VaR in dollars, VaR as % of portfolio value).
    """
    weights = _portfolio_weights(holdings)
    returns_df = pd.DataFrame({t: price_history[t] for t in weights.index if t in price_history})

    # align lengths defensively
    returns_df = returns_df.dropna()
    port_returns = returns_df[weights.index.intersection(returns_df.columns)].mul(
        weights[weights.index.intersection(returns_df.columns)], axis=1
    ).sum(axis=1)

    if port_returns.empty:
        return 0.0, 0.0

    loss_pct = -np.percentile(port_returns, (1 - confidence_level) * 100)
    pv = portfolio_value(holdings)
    var_dollars = max(loss_pct, 0) * pv
    return float(var_dollars), float(max(loss_pct, 0) * 100)


def sharpe_ratio(
    holdings: list[Holding],
    price_history: dict[str, list[float]],
    risk_free_rate: float = 0.04,
    trading_days: int = 252,
) -> float:
    weights = _portfolio_weights(holdings)
    returns_df = pd.DataFrame({t: price_history[t] for t in weights.index if t in price_history}).dropna()
    common = weights.index.intersection(returns_df.columns)
    if common.empty:
        return 0.0

    port_returns = returns_df[common].mul(weights[common], axis=1).sum(axis=1)
    mean_daily = port_returns.mean()
    std_daily = port_returns.std()

    if std_daily == 0 or np.isnan(std_daily):
        return 0.0

    annualized_return = mean_daily * trading_days
    annualized_vol = std_daily * np.sqrt(trading_days)
    return float((annualized_return - risk_free_rate) / annualized_vol)


def beta_weighted_exposure(holdings: list[Holding]) -> float:
    """Portfolio-level beta: weighted average of each holding's beta vs. benchmark."""
    weights = _portfolio_weights(holdings)
    betas = pd.Series({h.ticker: h.beta for h in holdings})
    return float((weights * betas).sum())


def sector_concentration(holdings: list[Holding]) -> dict[str, float]:
    weights = _portfolio_weights(holdings)
    sectors = pd.Series({h.ticker: h.sector for h in holdings})
    df = pd.DataFrame({"weight": weights, "sector": sectors})
    concentration = df.groupby("sector")["weight"].sum().sort_values(ascending=False)
    return {k: round(float(v) * 100, 2) for k, v in concentration.items()}


def correlation_matrix(price_history: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    returns_df = pd.DataFrame(price_history).dropna()
    if returns_df.shape[1] < 2:
        return {}
    corr = returns_df.corr().round(3)
    return {row: corr.loc[row].to_dict() for row in corr.index}


def compute_all_metrics(
    holdings: list[Holding],
    price_history: dict[str, list[float]],
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.04,
) -> RiskMetrics:
    var_dollars, var_pct = value_at_risk(holdings, price_history, confidence_level)

    return RiskMetrics(
        portfolio_value=round(portfolio_value(holdings), 2),
        value_at_risk_95=round(var_dollars, 2),
        value_at_risk_pct=round(var_pct, 2),
        sharpe_ratio=round(sharpe_ratio(holdings, price_history, risk_free_rate), 3),
        beta_weighted_exposure=round(beta_weighted_exposure(holdings), 3),
        sector_concentration=sector_concentration(holdings),
        correlation_matrix=correlation_matrix(price_history),
    )
