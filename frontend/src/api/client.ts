const API_BASE = import.meta.env.VITE_API_URL || "/api/v1"

type FetchOpts = RequestInit & { raw?: boolean }

class ApiError extends Error {
  status: number
  code?: string
  constructor(message: string, status: number, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

function getToken() {
  return localStorage.getItem("cnizos_access_token")
}

export async function apiFetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  }
  const token = getToken()
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(url, {
    ...opts,
    headers,
    credentials: "include",
  })

  if (!res.ok) {
    let detail = res.statusText
    let code: string | undefined
    try {
      const j = await res.json()
      detail = j.detail || j.message || detail
      code = j.code
    } catch {}
    throw new ApiError(detail, res.status, code)
  }

  if (opts.raw) return res as unknown as T
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
}
