import { describe, expect, it } from 'vitest'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import { selectAssessmentBatchById, selectD01BatchDetail } from './d01Selectors'

describe('D01 selectors', () => {
  it('resolves a canonical batch and derives instance quantity, scene, fields, and tree from one graph', () => {
    const detail = selectD01BatchDetail(
      CREATION_DEMO_PROJECT_ID,
      'fixture-batch-wood',
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
    )

    expect(detail?.batch.batch_id).toBe('fixture-batch-wood')
    expect(detail?.scene.scene_id).toBe('fixture-scene-roof')
    expect(detail?.quantity).toBe(2)
    expect(detail?.instances.map((instance) => instance.component_instance_id)).toEqual([
      'fixture-component-01', 'fixture-component-02',
    ])
    expect(detail?.verification_fields.map((field) => field.key)).toEqual([
      'fixing_method', 'hidden_damage', 'surface_treatment',
    ])
    expect(detail?.verification_fields[2].item).toBeNull()
    expect(detail?.tree.flatMap((material) => material.types.flatMap((type) => type.batches)).map((batch) => batch.batch_id)).toEqual([
      'fixture-batch-wood', 'fixture-batch-metal',
    ])
  })

  it('does not resolve a batch from another project or a batch whose Scene is missing', () => {
    expect(selectAssessmentBatchById('missing', creationDemoGraph.assessmentBatches)).toBeNull()
    expect(selectD01BatchDetail(
      'another-project',
      'fixture-batch-wood',
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
    )).toBeNull()
  })
})
