import { describe, expect, it } from 'vitest'
import { apiUrl, backendUrl, readJsonResponse } from './http'

describe('HTTP API helpers', () => {
  it('keeps same-origin FastAPI paths when no API origin is configured', () => {
    expect(apiUrl('/api/v1/demo/scenes')).toBe('/api/v1/demo/scenes')
    expect(backendUrl('/camera-assets/example.jpg')).toBe('/camera-assets/example.jpg')
  })

  it('reads an HTML error body once and surfaces that body instead of a stream-lock error', async () => {
    const response = new Response('<html>upstream unavailable</html>', {
      status: 502,
      statusText: 'Bad Gateway',
    })

    await expect(readJsonResponse(response, { errorMessage: '请求失败（502）' }))
      .rejects.toThrow('<html>upstream unavailable</html>')
    expect(response.bodyUsed).toBe(true)
  })

  it('parses a successful JSON response from the captured text', async () => {
    const response = new Response(JSON.stringify({ status: 'ok' }), { status: 200 })
    await expect(readJsonResponse<{ status: string }>(response, { errorMessage: '请求失败（200）' }))
      .resolves.toEqual({ status: 'ok' })
  })
})
