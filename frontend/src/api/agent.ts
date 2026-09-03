import type { AnalyzeRequest, AnalyzeResponse, ChatRequest, SSEEvent } from "@/types/api"

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
): AsyncGenerator<SSEEvent> {
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

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""

      let eventType = ""
      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim()
        } else if (line.startsWith("data:")) {
          const data = line.slice(5).trim()
          if (eventType === "message" || eventType === "error") {
            try {
              yield JSON.parse(data) as SSEEvent
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
