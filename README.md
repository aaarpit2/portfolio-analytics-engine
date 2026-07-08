# Portfolio Analytics Engine (AI-Generated Summaries)

An AI-powered portfolio analytics engine that computes real risk/exposure metrics
(VaR, Sharpe ratio, beta-weighted exposure, sector concentration, correlation matrices)
and uses a grounded RAG pipeline to turn those numbers into plain-language,
compliance-safe summaries for retail investors.

Core idea: **the LLM never guesses numbers.** All metrics are computed by the Python
analytics layer first. The LLM only narrates the structured output that's injected
into its prompt (grounded generation), which is what keeps the summaries numerically
accurate and reduces hallucination risk.

## Architecture

```
                 ┌─────────────────────┐
                 │   Market/Portfolio   │
                 │   Data (JSON/API)    │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  Analytics Engine     │  (app/analytics)
                 │  pandas/numpy:        │
                 │  VaR, Sharpe, beta,   │
                 │  sector concentration,│
                 │  correlation matrix   │
                 └──────────┬───────────┘
                            │ structured metrics (JSON)
                 ┌──────────▼───────────┐
                 │  Retrieval Layer      │  (app/rag/retriever.py)
                 │  builds grounded      │
                 │  context block        │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  Guardrailed Prompt   │  (app/rag/prompt_templates.py)
                 │  + Compliance Filter  │  (app/rag/guardrails.py)
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  LLM Client           │  (app/rag/llm_client.py)
                 │  Anthropic API        │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  Redis Cache          │  (app/cache)
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  FastAPI              │  (app/api/routes.py)
                 └───────────────────────┘
```

## Tech stack

- **Backend**: FastAPI (Python)
- **Analytics**: pandas, NumPy — VaR, Sharpe ratio, beta-weighted exposure, sector concentration, correlation matrices
- **LLM**: Anthropic API (Claude) via `anthropic` SDK
- **Grounding/RAG**: custom lightweight retriever (no vector DB needed yet — portfolio data is structured, not unstructured text; can swap in LangChain + a vector store later if you add unstructured docs like fund prospectuses)
- **Caching**: Redis (via `redis-py`)
- **Data**: local JSON fixtures for now (`data/sample_portfolio.json`), designed to swap in a live market data API (IEX Cloud / Polygon.io / Alpha Vantage — Bloomberg/Refinitiv need enterprise contracts, so start with one of these for a personal project)

## Quickest path: Docker Compose

Spins up Redis, the FastAPI backend, and the frontend together.

```bash
cp .env.example .env
# edit .env — set LLM_PROVIDER and the matching API key (see note below)
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Redis: localhost:6379 (exposed for local inspection with `redis-cli`)

The backend's `app/` folder is bind-mounted into the container, so code edits on
your machine take effect without rebuilding (uvicorn isn't run with `--reload` in
the container by default — add `--reload` to the `CMD` in `Dockerfile` if you want
that during active development).

Stop everything with `docker compose down` (add `-v` to also wipe the Redis volume).

## Frontend (standalone, without Docker)

`frontend/index.html` is a single-file static page — no build step, no framework.
It calls the backend directly from the browser.

```bash
cd frontend
python3 -m http.server 3000
```

Open http://localhost:3000, confirm the "API base" field points at your running
backend (default `http://127.0.0.1:8000`), click **Load sample**, then **Generate
summary**. It renders the computed risk metrics (VaR, Sharpe, beta exposure, sector
concentration, correlation matrix) alongside the AI-generated narrative summary.

## Manual local setup (no Docker)

### 1. Prerequisites
- Python 3.11+
- Redis running locally (`brew install redis` on Mac, or Docker: `docker run -p 6379:6379 redis`)
- An Anthropic API key: https://console.anthropic.com/

### 2. Clone/init and create a virtual environment
```bash
cd portfolio-analytics-engine
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# then edit .env and add your API key
```

By default the project uses Anthropic's **Claude Haiku 4.5** (`LLM_PROVIDER=anthropic`,
`ANTHROPIC_MODEL=claude-haiku-4-5-20251001`) — the cheapest current Claude model,
at roughly $1/$5 per million input/output tokens, versus $3/$15 for Sonnet or
$5/$25 for Opus. For a portfolio summary of this size, cost per request is a
fraction of a cent.

To use OpenAI instead — e.g. with an existing API key — set in `.env`:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini
```
GPT-5.4 Mini (~$0.75/$4.50 per million tokens) is OpenAI's low-cost tier that
still handles narrative generation well. GPT-5.4 Nano is even cheaper
(~$0.20/$1.25) if you want to push cost down further, at some quality cost —
worth testing against your own compliance requirements before relying on it.
Note: a ChatGPT subscription (Plus/Pro/Team) is billed separately from the OpenAI
**API**, which is pay-as-you-go against its own API key from
https://platform.openai.com/api-keys — your ChatGPT login doesn't automatically
grant API credits. Same is true in reverse for Anthropic: a Claude.ai subscription
doesn't include API access; that's a separate key from https://console.anthropic.com/.
Only one provider needs to be configured; you don't need both.

### 4. Run Redis (if not already running)
```bash
redis-server
```

### 5. Run the API
```bash
uvicorn app.main:app --reload --port 8000
```

Visit http://127.0.0.1:8000/docs for interactive Swagger UI.

### 6. Try it
```bash
curl -X POST http://127.0.0.1:8000/api/v1/portfolio/summary \
  -H "Content-Type: application/json" \
  -d @data/sample_portfolio.json
```

## Project layout

```
portfolio-analytics-engine/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # env/config loading
│   ├── models/schemas.py        # Pydantic request/response models
│   ├── analytics/
│   │   ├── portfolio_data.py    # loads/validates portfolio + market data
│   │   └── risk_metrics.py      # VaR, Sharpe, beta, sector concentration, correlation
│   ├── rag/
│   │   ├── retriever.py         # builds grounded context from computed metrics
│   │   ├── prompt_templates.py  # prompt construction
│   │   ├── guardrails.py        # compliance filtering (no "investment advice" language)
│   │   └── llm_client.py        # Anthropic API wrapper
│   ├── cache/redis_cache.py     # caching layer
│   └── api/routes.py            # FastAPI routes
├── tests/
│   └── test_risk_metrics.py
├── data/
│   └── sample_portfolio.json
├── frontend/
│   └── index.html               # single-file static dashboard (no build step)
├── Dockerfile                   # backend image
├── docker-compose.yml           # backend + redis + frontend
├── .dockerignore
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Compliance note

This project generates *descriptive* summaries of a portfolio's existing composition
and historical risk metrics — not recommendations, predictions, or advice. The
guardrails layer (`app/rag/guardrails.py`) strips/blocks forward-looking or prescriptive
language (e.g. "you should buy/sell", "will outperform"). This is not a substitute for
legal/compliance review if you ever take this beyond a personal project.

## Pushing to GitHub

```bash
cd portfolio-analytics-engine
git init
git add .
git commit -m "Initial scaffold: analytics engine + RAG summary pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/portfolio-analytics-engine.git
git push -u origin main
```
