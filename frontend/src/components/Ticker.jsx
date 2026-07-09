export default function Ticker({ holdings }) {
  if (!holdings || holdings.length === 0) {
    return (
      <div className="ticker">
        <span>Load a portfolio to populate holdings —</span>
      </div>
    );
  }

  return (
    <div className="ticker">
      {holdings.map((h) => (
        <span key={h.ticker}>
          <b>{h.ticker}</b> {h.sector} · {h.shares}sh @ ${h.price.toFixed(2)} ·
          β{h.beta}
        </span>
      ))}
    </div>
  );
}
