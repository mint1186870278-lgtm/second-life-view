import type {
  AssessmentBatch,
  AssessmentBatchId,
  ComponentInstance,
  EvidenceStatus,
  Pathway,
  ProjectId,
  ReviewStatus,
  Scene,
  SceneId,
  VerificationItem,
  VerificationItemId,
  VerificationStatus,
  VerificationType,
} from '../domain'
import {
  getActiveVerificationItemsForProject,
  getAttentionBatchCount,
  getBatchPendingVerificationCount,
  getBatchQuantity,
  getDistinctAffectedBatchCount,
  getProjectAssessmentBatchCount,
  getProjectSceneCount,
  getReviewedBatchCount,
  getVerificationTypeCounts,
  isActiveVerificationItem,
  selectProjectBatches,
  selectProjectVerificationItems,
  type VerificationTypeCounts,
} from './projectSelectors'

export interface W02DraftBatchReadModel {
  batch_id: AssessmentBatchId
  material_group: string
  component_type: string
  batch_label: string
  quantity: number
  scene_id: SceneId
  scene_name: string
  scene_index: number
  pathway: Pathway
  evidence_status: EvidenceStatus
  review_status: ReviewStatus
  pending_verification_count: number
  attention: boolean
  attention_reason?: string
}

export function selectW02DraftBatches(
  projectId: ProjectId,
  scenes: readonly Scene[],
  instances: readonly ComponentInstance[],
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
): W02DraftBatchReadModel[] {
  const projectScenes = scenes.filter((scene) => scene.project_id === projectId)
  const sceneById = new Map(projectScenes.map((scene, index) => [scene.scene_id, { scene, index }]))

  return selectProjectBatches(projectId, batches).flatMap((batch) => {
    const sceneEntry = sceneById.get(batch.scene_id)
    if (!sceneEntry) return []
    return [{
      batch_id: batch.batch_id,
      material_group: batch.material_group,
      component_type: batch.component_type,
      batch_label: batch.batch_label,
      quantity: getBatchQuantity(batch.batch_id, instances),
      scene_id: batch.scene_id,
      scene_name: sceneEntry.scene.name,
      scene_index: sceneEntry.index + 1,
      pathway: batch.pathway,
      evidence_status: batch.evidence_status,
      review_status: batch.review_status,
      pending_verification_count: getBatchPendingVerificationCount(batch.batch_id, items),
      attention: batch.attention,
      attention_reason: batch.attention_reason,
    }]
  })
}

export interface W02VerificationRowReadModel {
  verification_id: VerificationItemId
  batch_id: AssessmentBatchId
  material_group: string
  batch_label: string
  scene_id: SceneId
  scene_name: string
  scene_index: number
  field: string
  question: string
  verification_type: VerificationType
  status: VerificationStatus
  focus_target?: string
  discovered_at?: string
  discovered_source?: string
}

export function selectW02VerificationRows(
  projectId: ProjectId,
  scenes: readonly Scene[],
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
): W02VerificationRowReadModel[] {
  const sceneById = new Map(
    scenes
      .filter((scene) => scene.project_id === projectId)
      .map((scene, index) => [scene.scene_id, { scene, index }]),
  )
  const batchById = new Map(selectProjectBatches(projectId, batches).map((batch) => [batch.batch_id, batch]))

  return selectProjectVerificationItems(projectId, batches, items).flatMap((item) => {
    const batch = batchById.get(item.batch_id)
    const sceneEntry = batch ? sceneById.get(batch.scene_id) : undefined
    if (!batch || !sceneEntry) return []
    return [{
      verification_id: item.verification_id,
      batch_id: item.batch_id,
      material_group: batch.material_group,
      batch_label: batch.batch_label,
      scene_id: batch.scene_id,
      scene_name: sceneEntry.scene.name,
      scene_index: sceneEntry.index + 1,
      field: item.field,
      question: item.question,
      verification_type: item.verification_type,
      status: item.status,
      focus_target: item.focus_key,
      discovered_at: item.discovered_at,
      discovered_source: item.discovered_source,
    }]
  })
}

export interface W02ASummaryReadModel {
  assessment_batch_count: number
  reviewed_batch_count: number
  attention_batch_count: number
  scene_count: number
}

export function selectW02ASummary(
  projectId: ProjectId,
  scenes: readonly Scene[],
  batches: readonly AssessmentBatch[],
): W02ASummaryReadModel {
  return {
    assessment_batch_count: getProjectAssessmentBatchCount(projectId, batches),
    reviewed_batch_count: getReviewedBatchCount(projectId, batches),
    attention_batch_count: getAttentionBatchCount(projectId, batches),
    scene_count: getProjectSceneCount(projectId, scenes),
  }
}

export type W02BSummaryScope = 'active-task-context' | 'status-filtered-result'

export interface W02BSummaryOptions {
  /** Explicit policy seam: Product has not frozen the Status-filter behavior. */
  scope: W02BSummaryScope
  statusFilteredItems?: readonly VerificationItem[]
}

export interface W02BSummaryReadModel extends VerificationTypeCounts {
  verification_item_count: number
  affected_batch_count: number
}

export function selectW02BSummary(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
  options: W02BSummaryOptions,
): W02BSummaryReadModel {
  const summaryItems =
    options.scope === 'active-task-context'
      ? getActiveVerificationItemsForProject(projectId, batches, items)
      : selectProjectVerificationItems(projectId, batches, options.statusFilteredItems ?? items)
  return {
    verification_item_count: summaryItems.length,
    affected_batch_count: getDistinctAffectedBatchCount(summaryItems),
    ...getVerificationTypeCounts(summaryItems),
  }
}

export interface W02BMaterialGroup {
  material_group: string
  items: VerificationItem[]
  active_item_count: number
  affected_batch_count: number
}

export function selectW02BMaterialGroups(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
  visibleItems: readonly VerificationItem[],
  includeEmptyMaterials = false,
): W02BMaterialGroup[] {
  const projectBatches = selectProjectBatches(projectId, batches)
  const batchById = new Map(projectBatches.map((batch) => [batch.batch_id, batch]))
  const materials = new Map<string, VerificationItem[]>()

  if (includeEmptyMaterials) {
    projectBatches.forEach((batch) => materials.set(batch.material_group, []))
  }

  for (const item of visibleItems) {
    const batch = batchById.get(item.batch_id)
    if (!batch) continue
    const group = materials.get(batch.material_group) ?? []
    group.push(item)
    materials.set(batch.material_group, group)
  }

  return [...materials.entries()].map(([material_group, groupItems]) => {
    const activeItems = groupItems.filter(isActiveVerificationItem)
    return {
      material_group,
      items: groupItems,
      active_item_count: activeItems.length,
      affected_batch_count: getDistinctAffectedBatchCount(activeItems),
    }
  })
}
