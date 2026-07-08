from fastapi import APIRouter, HTTPException

from app.analytics.portfolio_data import validate_portfolio
from app.analytics.risk_metrics import compute_all_metrics
from app.cache.redis_cache import get_cached_summary, make_cache_key, set_cached_summary
from app.models.schemas import PortfolioRequest, PortfolioSummaryResponse
from app.rag.guardrails import enforce_guardrails
from app.rag.llm_client import generate_summary
from app.rag.retriever import build_grounded_context

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.post("/summary", response_model=PortfolioSummaryResponse)
def portfolio_summary(request: PortfolioRequest) -> PortfolioSummaryResponse:
    try:
        validate_portfolio(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cache_key = make_cache_key(request.portfolio_id, request.model_dump())
    cached = get_cached_summary(cache_key)
    if cached:
        return PortfolioSummaryResponse(**cached, cached=True)

    # 1. Structured analytics layer computes real numbers
    metrics = compute_all_metrics(
        holdings=request.holdings,
        price_history=request.price_history,
        confidence_level=request.confidence_level,
        risk_free_rate=request.risk_free_rate,
    )

    # 2. Build grounded context (the "retrieval" step for structured data)
    context = build_grounded_context(
        portfolio_id=request.portfolio_id,
        holdings=request.holdings,
        metrics=metrics,
        benchmark_ticker=request.benchmark_ticker,
    )

    # 3. LLM narrates only what it's given
    raw_summary = generate_summary(context)

    # 4. Guardrails enforce compliance-safe language
    safe_summary = enforce_guardrails(raw_summary)

    response = PortfolioSummaryResponse(
        portfolio_id=request.portfolio_id,
        metrics=metrics,
        summary=safe_summary,
        cached=False,
    )

    set_cached_summary(cache_key, response.model_dump(exclude={"cached"}))
    return response


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
