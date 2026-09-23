type ErrorMessageResolver = (body: unknown, rawBody: string, fallback: string) => string

interface ReadJsonOptions {
  errorMessage: string
  resolveErrorMessage?: ErrorMessageResolver
}

/**
 * Root URL for the FastAPI origin. It must be an origin (for example
 * `https://api.example.com`), not an `/api` endpoint. A terminal `/api` is
 * accepted too so a mistakenly included suffix cannot create `/api/api/...`.
 */
const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ?? ''
const fastApiOrigin = configuredApiBaseUrl
  .replace(/\/+$/, '')
  .replace(/\/api$/, '')

/** Build a FastAPI URL while preserving same-origin `/api` requests by default. */
export function apiUrl(path: string): string {
  const normalizedPath = `/${path.replace(/^\/+/, '')}`
  const apiPath = normalizedPath === '/api' || normalizedPath.startsWith('/api/')
    ? normalizedPath
    : `/api${normalizedPath}`
  return `${fastApiOrigin}${apiPath}`
}

/**
 * Resolve a relative URL returned by FastAPI (for example `/camera-assets/...`)
 * against the configured API origin. Absolute provider URLs remain untouched.
 */
export function backendUrl(url: string): string {
  if (!url || /^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(url)) return url
  return `${fastApiOrigin}/${url.replace(/^\/+/, '')}`
}

/**
 * Consume a Fetch response body exactly once, then parse the captured text as
 * JSON. Reading `response.json()` before trying `response.text()` leaves the
 * body locked when an HTML error response is returned by a static host.
 */
export async function readJsonResponse<T>(response: Response, options: ReadJsonOptions): Promise<T> {
  const rawBody = await response.text()
  let body: unknown
  let isJson = false

  if (rawBody.trim()) {
    try {
      body = JSON.parse(rawBody) as unknown
      isJson = true
    } catch {
      // Keep the raw response available for the actionable error below.
    }
  }

  if (!response.ok) {
    const message = options.resolveErrorMessage
      ? options.resolveErrorMessage(body, rawBody, options.errorMessage)
      : rawBody || options.errorMessage
    throw new Error(message || options.errorMessage)
  }

  if (!isJson) {
    throw new Error(`服务返回了非 JSON 响应（${response.status}）`)
  }

  return body as T
}
