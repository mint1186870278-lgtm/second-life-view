export interface DemoScene {
  id: string
  name: string
  filename: string
  asset_url: string
  thumbnail_url: string
  annotated_url: string
  width: number
  height: number
  size_bytes: number
  has_cached_yolo: boolean
  detection_count: number
  group_count: number
  category_counts: Record<string, number>
  default_selected: boolean
}

export interface DemoGroup {
  id: string
  group_name?: string
  label: string
  category: string
  material?: string
  scene_id: string
  scene_name: string
  confidence: number
  detected_count: number
  recommended_pathway?: string | null
  evidence_status?: string | null
  crop_url?: string
  can_generate_preview?: boolean
}

export interface DemoComponentEvidence {
  id: string
  note?: string | null
  image_url?: string | null
  filename?: string | null
  source: string
}

export interface DemoComponentLink {
  title: string
  description: string
  source_url: string
  provenance: 'verified' | 'inferred' | 'to_confirm'
}

export interface DemoComponentDetail {
  component: {
    id: string
    name: string
    category: string
    category_name: string
    material: string
    confidence: number
    detected_count: number
    evidence_status: string
    evidence_label: string
    recommended_pathway: string
    pathway_label: string
    crop_url: string
    preview_url: string
    can_generate_preview: boolean
  }
  scene: {
    id: string
    name: string
    asset_url: string
    annotated_url: string
  }
  region: string
  assessment: {
    title: string
    description: string
    pathway_label: string
    evidence_label: string
  }
  verification_questions: Array<{ title: string; description: string }>
  observable_facts: string[]
  reference_pathways: DemoComponentLink[]
  local_opportunities: DemoComponentLink[]
  three_d_url: string
  evidence: DemoComponentEvidence[]
}

export interface DemoComponentDesignAdvice {
  component_id: string
  crop_url: string
  scene_name: string
  title: string
  material: string
  color: string
  surface: string
  construction: string
  rationale: string
  provider: string
  status: string
  warning?: string
}

export interface DemoComponentPreview {
  component_id: string
  status: string
  provider: string
  prompt: string
  image_url: string
  is_offline_fallback: boolean
  generation_task_id?: string | null
}

export interface DemoStage {
  status: string
  provider: string
  message: string
}

export interface DemoDesign {
  title: string
  rationale: string
  prompt: string
  image_url?: string | null
  generation_task_id?: string | null
  constraints: string[]
  status: string
}

export interface DemoSpatialGeneration {
  status: string
  provider: string
  world_id?: string | null
  preview_url?: string | null
  message?: string | null
}

export interface DemoSource {
  title: string
  url: string
  snippet: string
  source_type: string
  confidence: number
  provenance: 'verified' | 'inferred' | 'to_confirm'
}

export interface DemoAgentEvent {
  timestamp: string
  agent: string
  action: string
  message: string
  data: Record<string, unknown>
}

export interface DemoAnalysisResult {
  run_id: string
  status: string
  scenes: DemoScene[]
  scene_count: number
  raw_detection_count: number
  component_count: number
  group_count: number
  category_counts: Record<string, number>
  evidence_checked_count: number
  pending_evidence_count: number
  groups: DemoGroup[]
  groups_truncated: number
  design?: DemoDesign | null
  spatial_generation: DemoSpatialGeneration
  stages: {
    preprocess: DemoStage
    perception: DemoStage
    evidence: DemoStage
    design: DemoStage
  }
  sources: DemoSource[]
  events: DemoAgentEvent[]
  errors: string[]
}

export interface DemoAnalyzeInput {
  scene_ids: string[]
  user_goal: string
  region?: string
  spatial_prompt: string
  include_web?: boolean
}

const fallbackSceneData = [
  ['0552569a06b61e4551697bd0f211286e', '屋顶露台', '0552569a06b61e4551697bd0f211286e.jpg', 7680, 3840, 51, 24],
  ['371eefc93daaebc61d98fb6ed1422691', '大堂休息区', '371eefc93daaebc61d98fb6ed1422691.jpg', 7680, 3840, 34, 15],
  ['822548005dbfc0c2a17d53647c5418f4', '餐饮接待区', '822548005dbfc0c2a17d53647c5418f4.jpg', 7680, 3840, 94, 42],
  ['c5492d66e5bcad84e73dc80dbb288a5f', '景观连廊', 'c5492d66e5bcad84e73dc80dbb288a5f.jpg', 7680, 3840, 52, 18],
  ['combination_room', '组合起居室', 'combination_room.jpg', 8192, 4096, 29, 19],
  ['d8bdc5c3e1e88f3672da35df425cca3c', '入口迎宾区', 'd8bdc5c3e1e88f3672da35df425cca3c.jpg', 2560, 1280, 30, 10],
  ['e82029f0f900bfd594d9c908060dacfe', '宴会休闲区', 'e82029f0f900bfd594d9c908060dacfe.jpg', 7680, 3840, 126, 46],
  ['en_suite', '套房卫浴', 'en_suite.jpg', 8192, 4096, 19, 13],
  ['hotel_room', '酒店客房', 'hotel_room.jpg', 8192, 4096, 26, 15],
  ['lythwood_lounge', '会客厅', 'lythwood_lounge.jpg', 8192, 4096, 112, 53],
  ['old_room', '历史空置厅', 'old_room.jpg', 8192, 4096, 16, 8],
] as const

export const fallbackDemoScenes: DemoScene[] = fallbackSceneData.map(([
  id,
  name,
  filename,
  width,
  height,
  detectionCount,
  groupCount,
], index) => ({
  id,
  name,
  filename,
  asset_url: `/demo-assets/${filename}`,
  thumbnail_url: `/api/v1/demo/scenes/${id}/thumbnail`,
  annotated_url: `/api/v1/demo/scenes/${id}/annotated`,
  width,
  height,
  size_bytes: 0,
  has_cached_yolo: true,
  detection_count: detectionCount,
  group_count: groupCount,
  category_counts: {},
  default_selected: index < 5,
}))

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const body = await response.json() as { detail?: string }
      message = body.detail ?? message
    } catch {
      const text = await response.text()
      if (text) message = text
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export async function fetchDemoScenes(): Promise<DemoScene[]> {
  const response = await fetch('/api/v1/demo/scenes')
  const payload = await readJson<{ scenes: DemoScene[] }>(response)
  return payload.scenes
}

export async function runDemoAnalysis(input: DemoAnalyzeInput): Promise<DemoAnalysisResult> {
  const response = await fetch('/api/v1/demo/analyze', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(input),
  })
  return readJson<DemoAnalysisResult>(response)
}

export async function fetchDemoReviewGroups(sceneIds: readonly string[] = []): Promise<DemoGroup[]> {
  const search = new URLSearchParams()
  sceneIds.forEach((sceneId) => search.append('scene_ids', sceneId))
  const suffix = search.size ? `?${search.toString()}` : ''
  const response = await fetch(`/api/v1/demo/components${suffix}`)
  const payload = await readJson<{ groups: DemoGroup[] }>(response)
  return payload.groups
}

export async function fetchDemoComponentDetail(groupId: string, region?: string): Promise<DemoComponentDetail> {
  const search = region ? `?${new URLSearchParams({ region }).toString()}` : ''
  const response = await fetch(`/api/v1/demo/components/${encodeURIComponent(groupId)}/detail${search}`)
  return readJson<DemoComponentDetail>(response)
}

export async function requestDemoComponentDesignAdvice(groupId: string, region?: string): Promise<DemoComponentDesignAdvice> {
  const response = await fetch(`/api/v1/demo/components/${encodeURIComponent(groupId)}/design-advice`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ region }),
  })
  return readJson<DemoComponentDesignAdvice>(response)
}

export async function generateDemoComponentPreview(
  groupId: string,
  advice: Pick<DemoComponentDesignAdvice, 'material' | 'color' | 'surface' | 'construction' | 'rationale'>,
  region?: string,
): Promise<DemoComponentPreview> {
  const response = await fetch(`/api/v1/demo/components/${encodeURIComponent(groupId)}/preview`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ region, advice }),
  })
  return readJson<DemoComponentPreview>(response)
}

export async function uploadDemoComponentEvidence(
  groupId: string,
  input: { file?: File; imageUrl?: string; note?: string },
): Promise<{ evidence: DemoComponentEvidence; count: number }> {
  const form = new FormData()
  if (input.file) form.append('file', input.file)
  if (input.imageUrl?.trim()) form.append('image_url', input.imageUrl.trim())
  if (input.note?.trim()) form.append('note', input.note.trim())
  const response = await fetch(`/api/v1/demo/components/${encodeURIComponent(groupId)}/evidence`, {
    method: 'POST',
    body: form,
  })
  return readJson<{ evidence: DemoComponentEvidence; count: number }>(response)
}
