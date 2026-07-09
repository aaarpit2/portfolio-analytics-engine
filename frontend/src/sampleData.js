const SAMPLE_HOLDINGS = [
  { ticker: "AAPL", sector: "Technology", shares: 50, price: 210.5, beta: 1.2 },
  { ticker: "MSFT", sector: "Technology", shares: 30, price: 445.2, beta: 1.1 },
  { ticker: "JNJ", sector: "Healthcare", shares: 40, price: 152.3, beta: 0.6 },
  { ticker: "JPM", sector: "Financials", shares: 25, price: 210.1, beta: 1.15 },
  { ticker: "XOM", sector: "Energy", shares: 35, price: 118.75, beta: 0.9 },
];

function genReturns(n, vol, drift) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    out.push(Number((drift + z * vol).toFixed(5)));
  }
  return out;
}

export function buildSamplePortfolio() {
  const price_history = {};
  SAMPLE_HOLDINGS.forEach((h) => {
    price_history[h.ticker] = genReturns(120, 0.015, 0.0004);
  });

  return {
    portfolio_id: "demo-portfolio-001",
    benchmark_ticker: "SPY",
    holdings: SAMPLE_HOLDINGS,
    price_history,
    benchmark_history: genReturns(120, 0.011, 0.0003),
    confidence_level: 0.95,
    risk_free_rate: 0.04,
  };
}
