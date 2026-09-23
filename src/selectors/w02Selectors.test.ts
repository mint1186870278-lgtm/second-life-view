import { describe, expect, it } from 'vitest'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import {
  selectW02ASummary,
  selectW02DraftBatches,
  selectW02VerificationRows,
} from './w02Selectors'

describe('W02 selectors', () => {
  it('derives the W02-A four-metric summary from canonical project data', () => {
    expect(selectW02ASummary(
      CREATION_DEMO_PROJECT_ID,
      creationDemoGraph.scenes,
      creationDemoGraph.assessmentBatches,
    )).toEqual({
      assessment_batch_count: 2,
      reviewed_batch_count: 1,
      attention_batch_count: 1,
      scene_count: 4,
    })
  })

  it('derives per-Batch pending counts from active VerificationItems', () => {
    const rows = selectW02DraftBatches(
      CREATION_DEMO_PROJECT_ID,
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
    )
    expect(rows.find((row) => row.batch_id === 'fixture-batch-wood')?.pending_verification_count).toBe(2)
    expect(rows.find((row) => row.batch_id === 'fixture-batch-metal')?.pending_verification_count).toBe(0)
  })

  it('projects VerificationItems with canonical batch and Scene identity', () => {
    const rows = selectW02VerificationRows(
      CREATION_DEMO_PROJECT_ID,
      creationDemoGraph.scenes,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
    )
    expect(rows[0]).toMatchObject({
      verification_id: 'fixture-verification-01',
      batch_id: 'fixture-batch-wood',
      scene_id: 'fixture-scene-roof',
      focus_target: 'fixing_method',
    })
  })
})
