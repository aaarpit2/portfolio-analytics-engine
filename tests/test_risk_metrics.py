import json
from pathlib import Path

from app.analytics.risk_metrics import compute_all_metrics
from app.models.schemas import Holding

FIXTURE = json.loads((Path(__file__).parent.parent / "data" / "sample_portfolio.json").read_text())


def _holdings():
    return [Holding(**h) for h in FIXTURE["holdings"]]


def test_portfolio_value_positive():
    metrics = compute_all_metrics(_holdings(), FIXTURE["price_history"])
    assert metrics.portfolio_value > 0


def test_sector_concentration_sums_to_100():
    metrics = compute_all_metrics(_holdings(), FIXTURE["price_history"])
    total = sum(metrics.sector_concentration.values())
    assert abs(total - 100) < 0.5


def test_var_is_non_negative():
    metrics = compute_all_metrics(_holdings(), FIXTURE["price_history"])
    assert metrics.value_at_risk_95 >= 0
    assert metrics.value_at_risk_pct >= 0


def test_beta_weighted_exposure_within_reasonable_range():
    metrics = compute_all_metrics(_holdings(), FIXTURE["price_history"])
    # all individual betas are between 0.6 and 1.2 in the fixture
    assert 0.5 <= metrics.beta_weighted_exposure <= 1.3


def test_correlation_matrix_has_all_tickers():
    metrics = compute_all_metrics(_holdings(), FIXTURE["price_history"])
    tickers = {h.ticker for h in _holdings()}
    assert set(metrics.correlation_matrix.keys()) == tickers
