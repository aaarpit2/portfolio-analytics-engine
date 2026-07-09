export default function InputPanel({
  payload,
  onPayloadChange,
  onLoadSample,
  onSubmit,
  apiBase,
  onApiBaseChange,
  status,
  loading,
}) {
  return (
    <div>
      <div className="panel-label">01 — Portfolio Payload (JSON)</div>
      <textarea
        spellCheck={false}
        value={payload}
        onChange={(e) => onPayloadChange(e.target.value)}
      />
      <div className="btn-row">
        <button type="button" className="secondary" onClick={onLoadSample}>
          Load sample
        </button>
        <button type="button" onClick={onSubmit} disabled={loading}>
          Generate summary
        </button>
      </div>
      <input
        id="apiBase"
        value={apiBase}
        onChange={(e) => onApiBaseChange(e.target.value)}
      />
      <div className={`status ${status.type || ""}`}>{status.message}</div>
    </div>
  );
}
