import type {
  AssessmentBatch,
  AssessmentBatchId,
  ComponentInstance,
  EvidenceStatus,
  Pathway,
  ProjectId,
  ReviewStatus,
  Scene,
  VerificationItem,
  VerificationStatus,
  VerificationType,
} from '../domain'
import {
  HUMAN_VERIFICATION_FIELD_KEYS,
  type HumanVerificationFieldKey,
} from '../domain'
import { getBatchQuantity, selectProjectBatches, selectProjectScenes } from './projectSelectors'

export const D01_PATHWAY_LABELS: Record<Pathway, string> = {
  KEEP_IN_PLACE: '原位保留',
  DIRECT_REUSE: '直接复用',
  REFURBISH: '修复翻新',
  REPURPOSE: '改作他用',
  MATERIAL_RECOVERY: '材料回收',
  DISPOSAL: '处置',
}

export const D01_EVIDENCE_LABELS: Record<EvidenceStatus, string> = {
  supported: '有依据',
  conditional: '条件性',
  insufficient_evidence: '证据不足',
  not_applicable: '不适用',
}

export const D01_REVIEW_LABELS: Record<ReviewStatus, string> = {
  unreviewed: '未审查',
  in_review: '审查中',
  reviewed: '已审查',
}

export const D01_VERIFICATION_STATUS_LABELS: Record<VerificationStatus, string> = {
  unverified: '待核实',
  unable_to_verify: '无法现场确认',
  verified: '已核实',
  not_applicable: '不适用',
}

export const D01_VERIFICATION_TYPE_LABELS: Record<VerificationType, string> = {
  onsite_observation: '现场观察',
  document_check: '文件核对',
  specialist_review: '专业复核',
}

export interface D01TreeBatch {
  batch_id: AssessmentBatchId
  label: string
  quantity: number
}

export interface D01TreeType {
  component_type: string
  batches: D01TreeBatch[]
}

export interface D01TreeMaterial {
  material_group: string
  types: D01TreeType[]
}

export interface D01VerificationFieldReadModel {
  key: HumanVerificationFieldKey
  item: VerificationItem | null
}

export interface D01BatchDetailReadModel {
  batch: AssessmentBatch
  scene: Scene
  scene_index: number
  instances: ComponentInstance[]
  quantity: number
  verification_items: VerificationItem[]
  verification_fields: D01VerificationFieldReadModel[]
  unmapped_verification_items: VerificationItem[]
  tree: D01TreeMaterial[]
}

export function selectAssessmentBatchById(
  batchId: AssessmentBatchId,
  batches: readonly AssessmentBatch[],
): AssessmentBatch | null {
  return batches.find((batch) => batch.batch_id === batchId) ?? null
}

export function selectD01BatchDetail(
  projectId: ProjectId,
  batchId: AssessmentBatchId,
  scenes: readonly Scene[],
  instances: readonly ComponentInstance[],
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
): D01BatchDetailReadModel | null {
  const projectBatches = selectProjectBatches(projectId, batches)
  const batch = selectAssessmentBatchById(batchId, projectBatches)
  if (!batch) return null

  const projectScenes = selectProjectScenes(projectId, scenes)
  const sceneIndex = projectScenes.findIndex((scene) => scene.scene_id === batch.scene_id)
  const scene = projectScenes[sceneIndex]
  if (!scene) return null

  const batchInstances = instances.filter((instance) => (
    instance.project_id === projectId && instance.batch_id === batch.batch_id
  ))
  const verificationItems = items.filter((item) => item.batch_id === batch.batch_id)
  const mappedKeys = new Set(
    verificationItems.flatMap((item) => (
      HUMAN_VERIFICATION_FIELD_KEYS.includes(item.focus_key as HumanVerificationFieldKey)
        ? [item.focus_key as HumanVerificationFieldKey]
        : []
    )),
  )

  const materialMap = new Map<string, Map<string, D01TreeBatch[]>>()
  projectBatches.forEach((candidate) => {
    const typeMap = materialMap.get(candidate.material_group) ?? new Map<string, D01TreeBatch[]>()
    const typeBatches = typeMap.get(candidate.component_type) ?? []
    typeBatches.push({
      batch_id: candidate.batch_id,
      label: candidate.batch_label,
      quantity: getBatchQuantity(candidate.batch_id, instances),
    })
    typeMap.set(candidate.component_type, typeBatches)
    materialMap.set(candidate.material_group, typeMap)
  })

  return {
    batch,
    scene,
    scene_index: sceneIndex + 1,
    instances: batchInstances,
    quantity: batchInstances.length,
    verification_items: verificationItems,
    verification_fields: HUMAN_VERIFICATION_FIELD_KEYS.map((key) => ({
      key,
      item: verificationItems.find((item) => item.focus_key === key) ?? null,
    })),
    unmapped_verification_items: verificationItems.filter((item) => (
      !item.focus_key || !mappedKeys.has(item.focus_key as HumanVerificationFieldKey)
    )),
    tree: [...materialMap].map(([material_group, typeMap]) => ({
      material_group,
      types: [...typeMap].map(([component_type, typeBatches]) => ({
        component_type,
        batches: typeBatches,
      })),
    })),
  }
}
