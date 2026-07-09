export default function SummaryCard({ summary }) {
  const paragraphs = summary.split(/\n{2,}/);

  return (
    <section className="fig">
      <div className="fig-label">FIG. 04 — AI-GENERATED SUMMARY</div>
      <div className="summary-card">
        {paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
    </section>
  );
}
