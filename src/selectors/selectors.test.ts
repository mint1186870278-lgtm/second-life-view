import { describe, expect, it } from 'vitest'
import { createTestGraph } from '../test/testGraph'
import {
  getActiveVerificationItemsForBatch,
  getActiveVerificationItemsForProject,
  getAttentionBatchCount,
  getBatchPendingVerificationCount,
  getBatchQuantity,
  getDistinctAffectedBatchCount,
  getProjectAssessmentBatchCount,
  getProjectComponentInstanceCount,
  getProjectSceneCount,
  getReviewedBatchCount,
  getVerificationTypeCounts,
  selectW02ASummary,
  selectW02BMaterialGroups,
  selectW02BSummary,
} from '.'

describe('canonical selectors', () => {
  it('derives project and batch counts from canonical entities', () => {
    const graph = createTestGraph()
    expect(getProjectSceneCount('p1', graph.scenes)).toBe(2)
    expect(getProjectComponentInstanceCount('p1', graph.componentInstances)).toBe(3)
    expect(getProjectAssessmentBatchCount('p1', graph.assessmentBatches)).toBe(2)
    expect(getReviewedBatchCount('p1', graph.assessmentBatches)).toBe(1)
    expect(getAttentionBatchCount('p1', graph.assessmentBatches)).toBe(1)
    expect(getBatchQuantity('b1', graph.componentInstances)).toBe(2)
  })

  it('isolates the active-status policy and derives verification counts', () => {
    const graph = createTestGraph()
    const batchItems = getActiveVerificationItemsForBatch('b1', graph.verificationItems)
    const projectItems = getActiveVerificationItemsForProject('p1', graph.assessmentBatches, graph.verificationItems)
    expect(batchItems.map((item) => item.verification_id)).toEqual(['v1', 'v2'])
    expect(projectItems).toHaveLength(2)
    expect(getBatchPendingVerificationCount('b1', graph.verificationItems)).toBe(2)
    expect(getDistinctAffectedBatchCount(projectItems)).toBe(1)
    expect(getVerificationTypeCounts(projectItems)).toEqual({
      onsite_observation: 1, document_check: 0, specialist_review: 1,
    })
  })

  it('builds the frozen W02-A summary', () => {
    const graph = createTestGraph()
    expect(selectW02ASummary('p1', graph.scenes, graph.assessmentBatches)).toEqual({
      assessment_batch_count: 2,
      reviewed_batch_count: 1,
      attention_batch_count: 1,
      scene_count: 2,
    })
  })

  it('requires an explicit W02-B summary scope policy', () => {
    const graph = createTestGraph()
    expect(selectW02BSummary('p1', graph.assessmentBatches, graph.verificationItems, {
      scope: 'active-task-context',
    })).toEqual({
      verification_item_count: 2,
      affected_batch_count: 1,
      onsite_observation: 1,
      document_check: 0,
      specialist_review: 1,
    })
    expect(selectW02BSummary('p1', graph.assessmentBatches, graph.verificationItems, {
      scope: 'status-filtered-result',
      statusFilteredItems: [graph.verificationItems[2]],
    }).verification_item_count).toBe(1)
  })

  it('groups W02-B items by canonical Batch material', () => {
    const graph = createTestGraph()
    const active = getActiveVerificationItemsForProject('p1', graph.assessmentBatches, graph.verificationItems)
    expect(selectW02BMaterialGroups('p1', graph.assessmentBatches, active, true)).toEqual([
      { material_group: 'Wood', items: active, active_item_count: 2, affected_batch_count: 1 },
      { material_group: 'Metal', items: [], active_item_count: 0, affected_batch_count: 0 },
    ])
  })
})
