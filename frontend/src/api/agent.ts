import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ChatRequest,
  SSEEvent,
  SSEFrame,
  SSEKnownEvent,
  SSEUnknown,
} from "@/types/api"

function getToken(): string | null {
  return localStorage.getItem("auth_token")
}

export async function analyzeMarket(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  const token = getToken()
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch("/api/v1/agent/analyze", {
    method: "POST",
    headers,
    body: JSON.stringify(request),
  })

  if (!res.ok) {
    const error = await res.json().catch(() => null)
    throw error || { error: { code: "UNKNOWN", message: `HTTP ${res.status}` } }
  }

  return res.json()
}

export async function* streamChat(
  request: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<SSEFrame> {
  const token = getToken()
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch("/api/v1/agent/chat", {
    method: "POST",
    headers,
    body: JSON.stringify(request),
    signal,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => null)
    throw error || { error: { code: "UNKNOWN", message: `HTTP ${res.status}` } }
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error("No response body")

  const decoder = new TextDecoder()
  let buffer = ""
  let eventType = ""
  let dataLines: string[] = []

  const KNOWN_TYPES = new Set<string>([
    "message_start",
    "tool_start",
    "tool_complete",
    "assistant_delta",
    "message_complete",
    "market_data",
    "error",
  ])

  function* flush(): Generator<SSEFrame> {
    if (eventType && dataLines.length > 0) {
      const raw = dataLines.join("\n")
      try {
        const parsed = JSON.parse(raw)
        if (typeof parsed === "object" && parsed !== null && typeof parsed.type === "string") {
          const event = parsed as SSEEvent
          if (KNOWN_TYPES.has(event.type)) {
            yield { known: true, event: event as SSEKnownEvent }
          } else {
            yield { known: false, event: event as SSEUnknown }
          }
        }
      } catch {
        // skip malformed JSON
      }
    }
    eventType = ""
    dataLines = []
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""

      for (const rawLine of lines) {
        const line = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine
        if (line === "") {
          yield* flush()
        } else if (line.startsWith("event:")) {
          yield* flush()
          eventType = line.slice(6).trim()
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart())
        }
        // ignore SSE comments (:...) and unknown fields
      }
    }
    if (buffer.trim() !== "") {
      const line = buffer.endsWith("\r") ? buffer.slice(0, -1) : buffer
      if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart())
      }
    }
    yield* flush()
  } finally {
    reader.releaseLock()
  }
}
