/**
 * Browser client for the loopback Windows CameraSDK gateway.
 *
 * This module intentionally contains no bearer token. The Windows companion
 * process keeps both the camera token and the Linux ingest token locally, and
 * permits this browser route only for its configured public web origin.
 */

import { readJsonResponse } from './http'

export interface WindowsCameraAsset {
  image_url: string
  frame_id?: string
  filename?: string
  size_bytes?: number
  original_filename?: string
  source?: string
}

export interface WindowsCameraYolo {
  source: string
  mode: 'live'
  detector: string
  device: string
  projection: string
  annotation_kind: string
  raw_detection_count: number
  component_group_count: number
  annotated_image_url: string
  detections_url: string
}

export interface WindowsCameraRun {
  run_id: string
  status: string
}

export interface WindowsCameraCaptureAndIngestResult {
  asset: WindowsCameraAsset
  yolo: WindowsCameraYolo
  run: WindowsCameraRun
  gateway: {
    frame_id?: string
    filename?: string
    camera?: { camera_name?: string; serial?: string }
    remote_paths?: string[]
  }
}

export interface BrowserCaptureInput {
  userGoal: string
  metadata: Record<string, unknown>
  outputWidth?: number
  outputHeight?: number
}

const BROWSER_CLIENT_HEADER = 'X-Second-Life-Client'
const browserGatewayBase = (
  import.meta.env.VITE_WINDOWS_CAMERA_GATEWAY_URL as string | undefined
)?.replace(/\/$/, '') ?? 'http://127.0.0.1:18080'

async function readJson<T>(response: Response): Promise<T> {
  return readJsonResponse<T>(response, {
    errorMessage: `Windows 相机网关请求失败（${response.status}）`,
    resolveErrorMessage: (body, rawBody, fallback) => {
      const detail = body && typeof body === 'object'
        ? (body as { detail?: unknown }).detail
        : undefined
      return typeof detail === 'string' ? detail : rawBody || fallback
    },
  })
}

export async function captureAndIngestFromWindows(
  input: BrowserCaptureInput,
): Promise<WindowsCameraCaptureAndIngestResult> {
  try {
    // Chromium's Local Network Access implementation recognizes this
    // opt-in for a public HTTPS page contacting loopback. Unsupported
    // browsers ignore the extra dictionary member and use normal CORS.
    const requestInit: RequestInit & { targetAddressSpace?: 'loopback' } = {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        [BROWSER_CLIENT_HEADER]: 'capture-ui-v1',
      },
      body: JSON.stringify({
        stitch: true,
        output_width: input.outputWidth ?? 4096,
        output_height: input.outputHeight ?? 2048,
        user_goal: input.userGoal,
        metadata: input.metadata,
      }),
      targetAddressSpace: 'loopback',
    }
    const response = await fetch(`${browserGatewayBase}/v1/browser/capture-and-ingest`, {
      ...requestInit,
    })
    return readJson<WindowsCameraCaptureAndIngestResult>(response)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        '无法访问本机相机网关。请确认 Windows Bridge 正在监听 127.0.0.1:18080，并在浏览器弹窗中允许此站点访问本地网络。',
      )
    }
    throw error
  }
}

export function windowsCameraGatewayBaseUrl(): string {
  return browserGatewayBase
}
