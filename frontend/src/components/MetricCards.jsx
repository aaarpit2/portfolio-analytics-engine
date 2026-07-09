function fmtUSD(n) {
  return (
    "$" +
    Number(n).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  );
}

export default function MetricCards({ metrics, cached }) {
  return (
    <section className="fig">
      <div className="fig-label">
        FIG. 01 — KEY METRICS {cached ? "(cached)" : ""}
      </div>
      <div className="metric-cards">
        <div className="metric-card">
          <div className="label">Portfolio Value</div>
          <div className="value">{fmtUSD(metrics.portfolio_value)}</div>
        </div>
        <div className="metric-card">
          <div className="label">VaR (95%, 1-day)</div>
          <div className="value brick">{fmtUSD(metrics.value_at_risk_95)}</div>
        </div>
        <div className="metric-card">
          <div className="label">VaR % of Portfolio</div>
          <div className="value brick">
            {metrics.value_at_risk_pct.toFixed(2)}%
          </div>
        </div>
        <div className="metric-card">
          <div className="label">Sharpe Ratio</div>
          <div className="value teal">{metrics.sharpe_ratio.toFixed(2)}</div>
        </div>
        <div className="metric-card">
          <div className="label">Beta-Weighted Exposure</div>
          <div className="value">
            {metrics.beta_weighted_exposure.toFixed(2)}
          </div>
        </div>
      </div>
    </section>
  );
}
