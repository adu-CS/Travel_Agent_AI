import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { sendMessage, resolveDownloadUrl, fetchPdfBlobUrl } from "./api.js";

const THREAD_STORAGE_KEY = "travel_agent_thread_id";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! Tell me about the trip you're planning \u2014 destination, dates or duration, and budget if you have one.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState(() => sessionStorage.getItem(THREAD_STORAGE_KEY));
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const [viewerUrl, setViewerUrl] = useState(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendMessage(text, threadId);

      if (!threadId && result.thread_id) {
        setThreadId(result.thread_id);
        sessionStorage.setItem(THREAD_STORAGE_KEY, result.thread_id);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.answer,
          pdfUrl: resolveDownloadUrl(result.pdf_path),
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleViewPdf(pdfUrl) {
  setError(null);
  try {
    const blobUrl = await fetchPdfBlobUrl(pdfUrl);
    setViewerUrl(blobUrl);
    } catch (err) {
      setError(err.message);
    }
  }

  function closeViewer() {
    if (viewerUrl) URL.revokeObjectURL(viewerUrl);
    setViewerUrl(null);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleNewTrip() {
    sessionStorage.removeItem(THREAD_STORAGE_KEY);
    setThreadId(null);
    setMessages([
      {
        role: "assistant",
        text: "New trip \u2014 where would you like to go?",
      },
    ]);
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Travel Agent</h1>
        <button className="new-trip-btn" onClick={handleNewTrip}>
          New trip
        </button>
      </header>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <ReactMarkdown>{m.text}</ReactMarkdown>
            {m.pdfUrl && (
              <button className="pdf-link" onClick={() => handleViewPdf(m.pdfUrl)}>
                View itinerary PDF
              </button>
            )}
          </div>
        ))}
        {loading && (
          <div className="message assistant loading">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}
        {error && <div className="error-banner">{error}</div>}
        <div ref={bottomRef} />
      </div>

      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. 6 day trip from Mumbai to Tokyo next month, budget friendly"
          rows={2}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
      {viewerUrl && (
        <div className="pdf-modal-backdrop" onClick={closeViewer}>
          <div className="pdf-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pdf-modal-header">
              <a href={viewerUrl} download="itinerary.pdf">Download</a>
              <button onClick={closeViewer}>Close</button>
            </div>
            <iframe src={viewerUrl} title="Itinerary PDF" />
          </div>
        </div>
      )}
    </div>
  );
}

