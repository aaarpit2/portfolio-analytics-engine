export default function SectorConcentration({ sectorConcentration }) {
  const rows = Object.entries(sectorConcentration).sort((a, b) => b[1] - a[1]);

  return (
    <section className="fig">
      <div className="fig-label">FIG. 02 — SECTOR CONCENTRATION</div>
      {rows.map(([sector, pct]) => (
        <div className="sector-row" key={sector}>
          <div className="sector-name">{sector}</div>
          <div className="sector-bar-track">
            <div className="sector-bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <div className="sector-pct">{pct.toFixed(1)}%</div>
        </div>
      ))}
    </section>
  );
}
