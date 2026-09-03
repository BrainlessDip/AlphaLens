const API_BASE = "/api/v1"

function getToken(): string | null {
  return localStorage.getItem("auth_token")
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => null)
    throw error || { error: { code: "UNKNOWN", message: `HTTP ${res.status}` } }
  }

  return res.json()
}
