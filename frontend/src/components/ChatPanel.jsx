import { useState } from "react";

export default function ChatPanel({ onSend, loading, result }) {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([]);

  const submit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    setHistory((h) => [...h, { role: "user", text: input }]);
    onSend(input);
    setInput("");
  };

  // Append the assistant's insight once a result comes back for the latest turn
  const displayHistory = [...history];
  if (result?.insight && displayHistory.length && displayHistory[displayHistory.length - 1].role === "user") {
    displayHistory.push({ role: "assistant", text: result.insight });
  }

  return (
    <>
      <div className="chat-log">
        {displayHistory.length === 0 && (
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
            Try: "How did the Northeast region do in 2026 Q2 versus target, and are there
            any contract terms or shelf issues I should know about?"
          </p>
        )}
        {displayHistory.map((m, i) => (
          <div className={`msg ${m.role}`} key={i}>
            {m.text}
          </div>
        ))}
      </div>
      <form className="composer" onSubmit={submit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about sales, contracts, or shelf compliance…"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Working…" : "Send"}
        </button>
      </form>
    </>
  );
}
