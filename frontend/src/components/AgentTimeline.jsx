const LABELS = {
  classify_intent: "Classifying intent",
  sql_node: "SQL agent — querying warehouse",
  doc_node: "Document agent — retrieving contract passages",
  vision_node: "Vision agent — analyzing shelf images",
  insight_node: "Insight agent — synthesizing findings",
  content_node: "Content agent — building report",
};

export default function AgentTimeline({ timeline, loading }) {
  if (timeline.length === 0 && !loading) {
    return <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Ask a question to see agents run here.</p>;
  }
  return (
    <div>
      {timeline.map((node, i) => (
        <div className="timeline-item" key={`${node}-${i}`}>
          <span className="dot" />
          {LABELS[node] || node}
        </div>
      ))}
      {loading && (
        <div className="timeline-item">
          <span className="dot" style={{ opacity: 0.4 }} />
          working…
        </div>
      )}
    </div>
  );
}
