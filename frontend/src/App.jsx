import { useState } from "react";
import Ticker from "./components/Ticker.jsx";
import InputPanel from "./components/InputPanel.jsx";
import MetricCards from "./components/MetricCards.jsx";
import SectorConcentration from "./components/SectorConcentration.jsx";
import CorrelationMatrix from "./components/CorrelationMatrix.jsx";
import SummaryCard from "./components/SummaryCard.jsx";
import { buildSamplePortfolio } from "./sampleData.js";

export default function App() {
  const initialSample = buildSamplePortfolio();

  const [payload, setPayload] = useState(
    JSON.stringify(initialSample, null, 2),
  );
  const [holdings, setHoldings] = useState(initialSample.holdings);
  const [apiBase, setApiBase] = useState("http://127.0.0.1:8000");
  const [status, setStatus] = useState({ message: "", type: "" });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleLoadSample = () => {
    const sample = buildSamplePortfolio();
    setPayload(JSON.stringify(sample, null, 2));
    setHoldings(sample.holdings);
    setStatus({ message: "Sample loaded.", type: "ok" });
  };

  const handleSubmit = async () => {
    let parsed;
    try {
      parsed = JSON.parse(payload);
    } catch (e) {
      setStatus({ message: "Invalid JSON payload.", type: "err" });
      return;
    }

    const base = apiBase.replace(/\/$/, "");
    setStatus({ message: "Requesting summary…", type: "" });
    setLoading(true);

    try {
      const res = await fetch(`${base}/api/v1/portfolio/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      setHoldings(parsed.holdings);
      setResult(data);
      setStatus({ message: "Done.", type: "ok" });
    } catch (e) {
      setStatus({
        message: e.message || "Request failed. Is the backend running?",
        type: "err",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">AI-Generated · Grounded in Computed Metrics</p>
        <h1 className="title">
          Portfolio <em>Ledger</em>
        </h1>
      </header>

      <Ticker holdings={holdings} />

      <div className="grid">
        <InputPanel
          payload={payload}
          onPayloadChange={setPayload}
          onLoadSample={handleLoadSample}
          onSubmit={handleSubmit}
          apiBase={apiBase}
          onApiBaseChange={setApiBase}
          status={status}
          loading={loading}
        />

        <div>
          {!result ? (
            <div className="empty-state">
              No results yet. Load the sample portfolio and click "Generate
              summary" — the backend must be running at the API base URL on the
              left.
            </div>
          ) : (
            <>
              <MetricCards metrics={result.metrics} cached={result.cached} />
              <SectorConcentration
                sectorConcentration={result.metrics.sector_concentration}
              />
              <CorrelationMatrix
                correlationMatrix={result.metrics.correlation_matrix}
              />
              <SummaryCard summary={result.summary} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
