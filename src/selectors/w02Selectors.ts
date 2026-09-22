import type {
  AssessmentBatch,
  ProjectId,
  Scene,
  VerificationItem,
} from '../domain'
import {
  getActiveVerificationItemsForProject,
  getAttentionBatchCount,
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
