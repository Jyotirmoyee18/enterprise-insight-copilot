export default function KpiPanel({ result }) {
  if (!result) return null;
  const rows = result.sql_result?.rows || [];

  return (
    <div>
      {rows.length > 0 && (
        <>
          <h2>KPIs</h2>
          {rows.map((r, i) => (
            <div className="kpi-card" key={i}>
              <div className="region">{r.region} · {r.quarter}</div>
              <div>
                ${r.revenue.toLocaleString()} revenue vs ${r.target.toLocaleString()} target
              </div>
              <div className={r.yoy_or_qoq_flag === "below_target" ? "flag-below" : "flag-ontrack"}>
                {r.attainment_pct}% attainment — {r.yoy_or_qoq_flag.replace("_", " ")}
              </div>
            </div>
          ))}
        </>
      )}

      {result.doc_result?.citations?.length > 0 && (
        <>
          <h2 style={{ marginTop: 20 }}>Contract citations</h2>
          {result.doc_result.citations.slice(0, 3).map((c, i) => (
            <div className="kpi-card" key={i}>
              <div className="region">{c.doc_id} · p.{c.page}</div>
              <div style={{ color: "var(--text-muted)" }}>{c.text}</div>
            </div>
          ))}
        </>
      )}

      {result.vision_result?.detections?.length > 0 && (
        <>
          <h2 style={{ marginTop: 20 }}>Shelf audit</h2>
          <div className="kpi-card">
            {result.vision_result.flagged_count} of {result.vision_result.detections.length} images flagged
          </div>
        </>
      )}

      {result.output_path && (
        <a className="download-btn" href={`/api/reports/${result.session_id}`}>
          Download report (.pptx)
        </a>
      )}

      <div style={{ marginTop: 20, fontSize: 11, color: "var(--text-muted)" }}>
        Est. cost this turn: ${result.cost_usd?.toFixed(4)}
      </div>
    </div>
  );
}
