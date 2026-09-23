import type {
  AssessmentBatch,
  AssessmentBatchId,
  ComponentInstance,
  ProjectId,
  Scene,
  VerificationItem,
  VerificationType,
} from '../domain'

export const ACTIVE_VERIFICATION_STATUSES = new Set(['unverified', 'unable_to_verify'] as const)

export function isActiveVerificationItem(item: VerificationItem): boolean {
  return ACTIVE_VERIFICATION_STATUSES.has(item.status as 'unverified' | 'unable_to_verify')
}

export function selectProjectScenes(projectId: ProjectId, scenes: readonly Scene[]): Scene[] {
  return scenes.filter((scene) => scene.project_id === projectId)
}

export function getProjectSceneCount(projectId: ProjectId, scenes: readonly Scene[]): number {
  return selectProjectScenes(projectId, scenes).length
}

export function getProjectComponentInstanceCount(
  projectId: ProjectId,
  instances: readonly ComponentInstance[],
): number {
  return instances.filter((instance) => instance.project_id === projectId).length
}

export function selectProjectBatches(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
): AssessmentBatch[] {
  return batches.filter((batch) => batch.project_id === projectId)
}

export function getProjectAssessmentBatchCount(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
): number {
  return selectProjectBatches(projectId, batches).length
}

export function getReviewedBatchCount(projectId: ProjectId, batches: readonly AssessmentBatch[]): number {
  return selectProjectBatches(projectId, batches).filter((batch) => batch.review_status === 'reviewed').length
}

export function getAttentionBatchCount(projectId: ProjectId, batches: readonly AssessmentBatch[]): number {
  return selectProjectBatches(projectId, batches).filter((batch) => batch.attention).length
}

export function getBatchQuantity(
  batchId: AssessmentBatchId,
  instances: readonly ComponentInstance[],
): number {
  return instances.filter((instance) => instance.batch_id === batchId).length
}

export function getActiveVerificationItemsForBatch(
  batchId: AssessmentBatchId,
  items: readonly VerificationItem[],
): VerificationItem[] {
  return items.filter((item) => item.batch_id === batchId && isActiveVerificationItem(item))
}

export function selectProjectVerificationItems(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
): VerificationItem[] {
  const batchIds = new Set(selectProjectBatches(projectId, batches).map((batch) => batch.batch_id))
  return items.filter((item) => batchIds.has(item.batch_id))
}

export function getActiveVerificationItemsForProject(
  projectId: ProjectId,
  batches: readonly AssessmentBatch[],
  items: readonly VerificationItem[],
): VerificationItem[] {
  return selectProjectVerificationItems(projectId, batches, items).filter(isActiveVerificationItem)
}

export function getBatchPendingVerificationCount(
  batchId: AssessmentBatchId,
  items: readonly VerificationItem[],
): number {
  return getActiveVerificationItemsForBatch(batchId, items).length
}

export function getDistinctAffectedBatchCount(items: readonly VerificationItem[]): number {
  return new Set(items.map((item) => item.batch_id)).size
}

export type VerificationTypeCounts = Record<VerificationType, number>

export function getVerificationTypeCounts(items: readonly VerificationItem[]): VerificationTypeCounts {
  return items.reduce<VerificationTypeCounts>(
    (counts, item) => {
      counts[item.verification_type] += 1
      return counts
    },
    { onsite_observation: 0, document_check: 0, specialist_review: 0 },
  )
}
