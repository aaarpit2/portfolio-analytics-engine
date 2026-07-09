export default function CorrelationMatrix({ correlationMatrix }) {
  const tickers = Object.keys(correlationMatrix);

  return (
    <section className="fig">
      <div className="fig-label">FIG. 03 — CORRELATION MATRIX</div>
      {tickers.length === 0 ? (
        <div className="empty-state">
          Not enough series to compute correlations.
        </div>
      ) : (
        <table className="corr">
          <thead>
            <tr>
              <th></th>
              {tickers.map((t) => (
                <th key={t}>{t}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map((row) => (
              <tr key={row}>
                <td>{row}</td>
                {tickers.map((col) => (
                  <td key={col}>
                    {correlationMatrix[row][col]?.toFixed(3) ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
