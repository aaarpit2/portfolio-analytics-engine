"""
This is the "R" in RAG: instead of retrieving unstructured documents from a vector
store, we retrieve/assemble the structured, already-computed metrics into a compact,
LLM-readable context block. The LLM is never asked to compute or recall numbers —
only to narrate numbers it's handed.

If you later add unstructured sources (fund prospectuses, news, filings), this is
where you'd add a vector-store lookup (LangChain + Chroma/FAISS/Pinecone) and merge
those retrieved chunks into the same context block.
"""

from app.models.schemas import Holding, RiskMetrics


def build_grounded_context(
    portfolio_id: str,
    holdings: list[Holding],
    metrics: RiskMetrics,
    benchmark_ticker: str,
) -> str:
    holdings_lines = "\n".join(
        f"- {h.ticker} ({h.sector}): {h.shares} shares @ ${h.price:.2f}, beta={h.beta}"
        for h in holdings
    )

    sector_lines = "\n".join(
        f"- {sector}: {weight}%" for sector, weight in metrics.sector_concentration.items()
    )

    context = f"""PORTFOLIO ID: {portfolio_id}
BENCHMARK: {benchmark_ticker}

HOLDINGS:
{holdings_lines}

COMPUTED RISK METRICS (ground truth — do not recalculate or contradict these):
- Total portfolio value: ${metrics.portfolio_value:,.2f}
- 1-day Value at Risk (95% confidence): ${metrics.value_at_risk_95:,.2f} ({metrics.value_at_risk_pct}% of portfolio)
- Sharpe ratio: {metrics.sharpe_ratio}
- Beta-weighted exposure vs {benchmark_ticker}: {metrics.beta_weighted_exposure}
- Sector concentration:
{sector_lines}
"""
    return context
