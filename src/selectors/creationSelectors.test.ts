import { describe, expect, it } from 'vitest'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import { buildCreationAnalysisSummary } from './creationSelectors'

describe('Creation analysis read model', () => {
  it('derives every visible C03 count from the canonical fixture graph', () => {
    const summary = buildCreationAnalysisSummary(
      CREATION_DEMO_PROJECT_ID,
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
    )

    expect(summary).toMatchObject({
      sceneCount: 4,
      componentCount: 4,
      assessmentBatchCount: 2,
      activeVerificationItemCount: 2,
    })
    expect(summary.processedScenes.map((scene) => scene.ingestion_status)).toEqual([
      'received', 'received', 'received', 'received',
    ])
  })
})
