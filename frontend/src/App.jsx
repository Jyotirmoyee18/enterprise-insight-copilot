import { useMemo } from "react";
import ChatPanel from "./components/ChatPanel.jsx";
import AgentTimeline from "./components/AgentTimeline.jsx";
import KpiPanel from "./components/KpiPanel.jsx";
import { useAgentStream } from "./hooks/useAgentStream.js";

export default function App() {
  const sessionId = useMemo(() => `session-${Math.random().toString(36).slice(2, 10)}`, []);
  const { timeline, result, loading, send } = useAgentStream();

  return (
    <div className="app">
      <div className="main-col">
        <div className="header">
          <h1>Enterprise Insight Copilot</h1>
          <p>Multi-agent BI &amp; reporting — LangGraph orchestration, cost-tiered models</p>
        </div>
        <ChatPanel onSend={(q) => send(sessionId, q)} loading={loading} result={result} />
      </div>
      <div className="side-col">
        <h2>Agent activity</h2>
        <AgentTimeline timeline={timeline} loading={loading} />
        <div style={{ marginTop: 24 }}>
          <KpiPanel result={result} />
        </div>
      </div>
    </div>
  );
}
