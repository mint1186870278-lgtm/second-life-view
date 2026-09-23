/** Local Capture Bridge client (Insta360 one-click capture). */

import { readJsonResponse } from './http'

export interface CaptureBridgeHealth {
  ok: boolean
  sdk_version: string
  camera_connected: boolean
  camera_model?: string | null
  firmware?: string | null
  backend: string
  detail?: string | null
}

export interface CaptureBridgeResult {
  capture_id: string
  status: string
  local_path?: string | null
  preview_url?: string | null
  width?: number | null
  height?: number | null
  file_size_bytes?: number | null
  mime_type?: string
  project_id?: string | null
  scene_label?: string | null
  meta?: {
    source_type?: string
    camera_model?: string
    sdk_version?: string
    in_camera_stitch?: boolean
    camera_file?: string | null
    backend?: string | null
  } | null
  error_code?: string | null
  error_message?: string | null
}

const BRIDGE_BASE = (import.meta.env.VITE_CAPTURE_BRIDGE_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'http://127.0.0.1:18765'

function formatDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object') {
    const body = detail as { error_message?: string; error_code?: string; msg?: string }
    if (body.error_message) {
      return body.error_code ? `${body.error_code}: ${body.error_message}` : body.error_message
    }
    if (body.msg) return body.msg
  }
  return fallback
}

async function readJson<T>(response: Response): Promise<T> {
  return readJsonResponse<T>(response, {
    errorMessage: `采集服务请求失败（${response.status}）`,
    resolveErrorMessage: (body, rawBody, fallback) => {
      const detail = body && typeof body === 'object'
        ? (body as { detail?: unknown }).detail
        : undefined
      return detail === undefined ? rawBody || fallback : formatDetail(detail, fallback)
    },
  })
}

export async function fetchCaptureBridgeHealth(): Promise<CaptureBridgeHealth> {
  const response = await fetch(`${BRIDGE_BASE}/health`, { signal: AbortSignal.timeout(5000) })
  return readJson<CaptureBridgeHealth>(response)
}

export async function startCaptureImport(input: {
  project_id: string
  scene_label?: string
}): Promise<CaptureBridgeResult> {
  const response = await fetch(`${BRIDGE_BASE}/import/latest`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      project_id: input.project_id,
      scene_label: input.scene_label ?? '',
      options: {
        photo_mode: 'pano',
        require_in_camera_stitch: true,
      },
    }),
  })
  return readJson<CaptureBridgeResult>(response)
}

export function captureBridgeBaseUrl(): string {
  return BRIDGE_BASE
}
