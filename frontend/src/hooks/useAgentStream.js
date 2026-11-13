import { useCallback, useRef, useState } from "react";

/**
 * Sends a query to the copilot and streams per-agent progress events over
 * SSE. Falls back gracefully if EventSource isn't available for the given
 * request (e.g. some proxies) -- callers can also just POST /api/chat for
 * a single non-streaming response.
 */
export function useAgentStream() {
  const [timeline, setTimeline] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const controllerRef = useRef(null);

  const send = useCallback(async (sessionId, query) => {
    setLoading(true);
    setTimeline([]);
    setResult(null);
    controllerRef.current = new AbortController();

    try {
      const resp = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, query }),
        signal: controllerRef.current.signal,
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop();

        for (const raw of events) {
          const dataLine = raw.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          const data = JSON.parse(dataLine.replace("data:", "").trim());
          if (data.node) {
            setTimeline((prev) => [...prev, data.node]);
          }
        }
      }

      // Fetch the final structured result via the non-streaming endpoint's
      // twin -- in this scaffold we simply re-fetch full state for display.
      const finalResp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, query }),
      });
      setResult(await finalResp.json());
    } catch (err) {
      if (err.name !== "AbortError") console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  return { timeline, result, loading, send };
}
