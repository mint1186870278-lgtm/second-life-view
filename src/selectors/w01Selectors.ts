import type {
  AssessmentBatch,
  AssessmentBatchId,
  ComponentInstance,
  EvidenceStatus,
  Pathway,
  ProjectId,
  Scene,
  SceneId,
  VerificationItem,
} from '../domain'
import {
  getActiveVerificationItemsForBatch,
  getBatchQuantity,
  getProjectComponentInstanceCount,
  selectProjectBatches,
  selectProjectScenes,
} from './projectSelectors'

export type W01HotspotTone = 'amber' | 'green' | 'blue' | 'gray'

export interface W01HotspotPlacement {
  batch_id: AssessmentBatchId
  x_percent: number
  y_percent: number
  tone: W01HotspotTone
}

export interface W01DemoSummaryRow {
  label: string
  value: string
  tone: 'green' | 'blue' | 'amber' | 'gray'
}

export interface W01DemoGroupRow {
  label: string
  quantity_label: string
  tone: string
}

export interface W01DemoHotspotRow {
  presentation_id: string
  scene_id: SceneId
  batch_id?: AssessmentBatchId
  label: string
  quantity: number
  x_percent: number
  y_percent: number
  tone: W01HotspotTone
}

export interface W01DemoTaskRow {
  label: string
  tone: W01HotspotTone
  focus_target?: string
}

export interface W01DemoProjection {
  hotspot_placements: readonly W01HotspotPlacement[]
  hotspot_rows: readonly W01DemoHotspotRow[]
  task_rows: readonly W01DemoTaskRow[]
  detected_component_count: number
  coarse_summary: readonly W01DemoSummaryRow[]
  group_rows: readonly W01DemoGroupRow[]
  potential: { value: string; copy: string }
  filmstrip_fillers: readonly { label: string; tone: number }[]
}

export interface W01FilmstripItem {
  scene_id: SceneId
  name: string
  ingestion_status: Scene['ingestion_status']
  visual_tone: number
  image_url?: string
  annotated_image_url?: string
  annotation_groups?: readonly W01AnnotationGroup[]
}

export interface W01AnnotationGroup {
  id: string
  name: string
  category: string
  quantity: number
}

export interface W01HotspotReadModel {
  batch_id: AssessmentBatchId
  label: string
  quantity: number
  x_percent: number
  y_percent: number
  tone: W01HotspotTone
}

export interface W01TaskReadModel {
  verification_id: VerificationItem['verification_id']
  batch_id: AssessmentBatchId
  label: string
  focus_target?: string
  status: VerificationItem['status']
}

export interface W01AssessmentReadModel {
  batch_id: AssessmentBatchId
  label: string
  material_group: string
  pathway: Pathway
  pathway_label: string
  evidence_status: EvidenceStatus
  evidence_label: string
}

export interface W01SceneReadModel {
  component_count: number
  selected_scene: Scene | null
  filmstrip: W01FilmstripItem[]
  hotspots: W01HotspotReadModel[]
  tasks: W01TaskReadModel[]
  assessment: W01AssessmentReadModel | null
}

const pathwayLabels: Record<Pathway, string> = {
  KEEP_IN_PLACE: '原位保留',
  DIRECT_REUSE: '直接复用',
  REFURBISH: '修复翻新',
  REPURPOSE: '改作他用',
  MATERIAL_RECOVERY: '材料回收',
  DISPOSAL: '处置',
}

const evidenceLabels: Record<EvidenceStatus, string> = {
  supported: '证据支持',
  conditional: '有条件支持',
  insufficient_evidence: '证据不足',
  not_applicable: '不适用',
}

export function selectW01SceneReadModel(
  projectId: ProjectId,
  selectedSceneId: SceneId | undefined,
  scenes: readonly Scene[],
  instances: readonly ComponentInstance[],
  batches: readonly AssessmentBatch[],
  verificationItems: readonly VerificationItem[],
  hotspotPlacements: readonly W01HotspotPlacement[],
): W01SceneReadModel {
  const projectScenes = selectProjectScenes(projectId, scenes)
  const selectedScene = projectScenes.find((scene) => scene.scene_id === selectedSceneId)
    ?? projectScenes[0]
    ?? null
  const projectBatches = selectProjectBatches(projectId, batches)
  const sceneBatches = selectedScene
    ? projectBatches.filter((batch) => batch.scene_id === selectedScene.scene_id)
    : []
  const placementByBatch = new Map(hotspotPlacements.map((placement) => [placement.batch_id, placement]))

  const hotspots = sceneBatches.flatMap<W01HotspotReadModel>((batch) => {
    const placement = placementByBatch.get(batch.batch_id)
    if (!placement) return []
    return [{
      batch_id: batch.batch_id,
      label: batch.batch_label,
      quantity: getBatchQuantity(batch.batch_id, instances),
      x_percent: placement.x_percent,
      y_percent: placement.y_percent,
      tone: placement.tone,
    }]
  })

  const tasks = sceneBatches.flatMap<W01TaskReadModel>((batch) => (
    getActiveVerificationItemsForBatch(batch.batch_id, verificationItems).map((item) => ({
      verification_id: item.verification_id,
      batch_id: batch.batch_id,
      label: item.question,
      focus_target: item.focus_key,
      status: item.status,
    }))
  ))

  const assessmentBatch = sceneBatches[0]
  const assessment = assessmentBatch ? {
    batch_id: assessmentBatch.batch_id,
    label: assessmentBatch.batch_label,
    material_group: assessmentBatch.material_group,
    pathway: assessmentBatch.pathway,
    pathway_label: pathwayLabels[assessmentBatch.pathway],
    evidence_status: assessmentBatch.evidence_status,
    evidence_label: evidenceLabels[assessmentBatch.evidence_status],
  } : null

  return {
    component_count: getProjectComponentInstanceCount(projectId, instances),
    selected_scene: selectedScene,
    filmstrip: projectScenes.map((scene, index) => ({
      scene_id: scene.scene_id,
      name: scene.name,
      ingestion_status: scene.ingestion_status,
      visual_tone: index % 4,
    })),
    hotspots,
    tasks,
    assessment,
  }
}
