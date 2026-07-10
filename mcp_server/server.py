"""
MCP (Model Context Protocol) server for the portfolio analytics engine.

Exposes the same analytics + RAG pipeline used by the FastAPI backend as MCP
tools, so any MCP-compatible AI assistant (Claude Desktop, Claude Code, etc.)
can call directly into real enterprise portfolio data and computed risk metrics
instead of the assistant guessing or being fed static sample data.

Security note: this is a locally-run reference implementation. Each tool call
is gated behind an API key checked against PORTFOLIO_MCP_API_KEY (set that env
var to enable the check; leave it unset for local/dev use). For a real
production deployment fronting enterprise systems, put this behind a proper
auth layer at the transport level (OAuth, mTLS, or an API gateway) rather than
relying solely on this per-call key check — this key check is a baseline
guard, not a substitute for transport-level security.
"""

import json
import os
import sys
from pathlib import Path

# Make the sibling `app` package importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from app.analytics.risk_metrics import compute_all_metrics
from app.models.schemas import Holding
from app.rag.guardrails import enforce_guardrails
from app.rag.llm_client import generate_summary
from app.rag.retriever import build_grounded_context

REQUIRED_API_KEY = os.environ.get("PORTFOLIO_MCP_API_KEY", "")
SAMPLE_PORTFOLIO_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_portfolio.json"

mcp = FastMCP("portfolio-analytics")


def _authorize(api_key: str) -> None:
    """Rejects the call if PORTFOLIO_MCP_API_KEY is configured and doesn't match."""
    if REQUIRED_API_KEY and api_key != REQUIRED_API_KEY:
        raise PermissionError(
            "Unauthorized: missing or invalid api_key for the portfolio-analytics MCP server."
        )


def _parse_holdings(data: dict) -> list[Holding]:
    try:
        return [Holding(**h) for h in data["holdings"]]
    except KeyError as e:
        raise ValueError(f"Portfolio JSON is missing required field: {e}")


@mcp.tool()
def compute_risk_metrics(portfolio_json: str, api_key: str = "") -> str:
    """
    Compute quantitative risk metrics for a portfolio: Value at Risk (VaR),
    Sharpe ratio, beta-weighted exposure, sector concentration, and a
    correlation matrix across holdings.

    Args:
        portfolio_json: JSON string with fields: portfolio_id, benchmark_ticker,
            holdings (list of {ticker, sector, shares, price, beta}),
            price_history (dict of ticker -> list of daily returns),
            benchmark_history (list of daily returns), confidence_level,
            risk_free_rate.
        api_key: Required if the server has PORTFOLIO_MCP_API_KEY configured.

    Returns:
        JSON string of computed RiskMetrics.
    """
    _authorize(api_key)
    data = json.loads(portfolio_json)
    holdings = _parse_holdings(data)

    metrics = compute_all_metrics(
        holdings=holdings,
        price_history=data["price_history"],
        confidence_level=data.get("confidence_level", 0.95),
        risk_free_rate=data.get("risk_free_rate", 0.04),
    )
    return metrics.model_dump_json(indent=2)


@mcp.tool()
def generate_portfolio_summary(portfolio_json: str, api_key: str = "") -> str:
    """
    Generate a plain-language, compliance-guardrailed AI summary of a
    portfolio's performance, sector/asset exposure, and risk concentration.
    Risk metrics are computed first (deterministic, real math) and injected
    into the LLM prompt as grounded context — the model narrates the numbers,
    it does not calculate or guess them.

    Args:
        portfolio_json: Same schema as compute_risk_metrics.
        api_key: Required if the server has PORTFOLIO_MCP_API_KEY configured.

    Returns:
        Plain-language summary text, with compliance guardrails applied
        (no advisory/predictive language, disclaimer appended).
    """
    _authorize(api_key)
    data = json.loads(portfolio_json)
    holdings = _parse_holdings(data)

    metrics = compute_all_metrics(
        holdings=holdings,
        price_history=data["price_history"],
        confidence_level=data.get("confidence_level", 0.95),
        risk_free_rate=data.get("risk_free_rate", 0.04),
    )

    context = build_grounded_context(
        portfolio_id=data.get("portfolio_id", "unknown"),
        holdings=holdings,
        metrics=metrics,
        benchmark_ticker=data.get("benchmark_ticker", "SPY"),
    )

    raw_summary = generate_summary(context)
    return enforce_guardrails(raw_summary)


@mcp.tool()
def get_sample_portfolio(api_key: str = "") -> str:
    """
    Return a sample portfolio JSON payload, useful for testing the other
    tools without needing a real enterprise data connection.

    Args:
        api_key: Required if the server has PORTFOLIO_MCP_API_KEY configured.
    """
    _authorize(api_key)
    return SAMPLE_PORTFOLIO_PATH.read_text()


if __name__ == "__main__":
    # stdio transport — the standard mode for local MCP clients like
    # Claude Desktop or Claude Code, which spawn this process directly.
    mcp.run(transport="stdio")