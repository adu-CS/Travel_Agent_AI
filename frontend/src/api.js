const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function sendMessage(message, threadId) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (res.status === 429) {
    throw new Error("You're sending messages too fast. Please wait a moment and try again.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Something went wrong. Please try again.");
  }
  return res.json();
}

export function resolveDownloadUrl(pdfPath) {
  if (!pdfPath) return null;
  if (pdfPath.startsWith("http")) return pdfPath; // already a presigned S3 URL
  if (pdfPath.startsWith("PDF generation failed")) return null;
  // local-disk fallback path, e.g. "outputs/itinerary_abc123.pdf"
  const filename = pdfPath.split(/[\\/]/).pop();
  return `${API_URL}/download/${encodeURIComponent(filename)}`;                               
}

export async function fetchPdfBlobUrl(url) {
  const res = await fetch(url);
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body.detail || "";
    } catch {
      // response wasn't JSON (e.g. an S3 XML error) — ignore
    }
    throw new Error(`Could not load the PDF (status ${res.status}). ${detail}`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}