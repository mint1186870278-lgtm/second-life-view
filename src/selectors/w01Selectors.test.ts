import { describe, expect, it } from 'vitest'
import { w01DemoProjection } from '../config'
import { PATHWAYS } from '../domain'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import { selectW01SceneReadModel } from './w01Selectors'

describe('W01 read models', () => {
  it('derives scene hotspots and quantities from canonical IDs', () => {
    const result = selectW01SceneReadModel(
      CREATION_DEMO_PROJECT_ID,
      'fixture-scene-roof',
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
      w01DemoProjection.hotspot_placements,
    )

    expect(result.selected_scene?.scene_id).toBe('fixture-scene-roof')
    expect(result.hotspots).toEqual([expect.objectContaining({
      batch_id: 'fixture-batch-wood',
      quantity: 2,
    })])
    expect(result.tasks.map((task) => task.focus_target)).toEqual(['fixing_method', 'hidden_damage'])
  })

  it('does not invent hotspots when a scene has no canonical placed batch', () => {
    const result = selectW01SceneReadModel(
      CREATION_DEMO_PROJECT_ID,
      'fixture-scene-entry',
      creationDemoGraph.scenes,
      creationDemoGraph.componentInstances,
      creationDemoGraph.assessmentBatches,
      creationDemoGraph.verificationItems,
      w01DemoProjection.hotspot_placements,
    )

    expect(result.hotspots).toEqual([])
    expect(result.tasks).toEqual([])
    expect(result.assessment).toBeNull()
  })

  it('keeps unresolved W01 summaries outside formal Pathway semantics', () => {
    expect(w01DemoProjection.coarse_summary.map((row) => row.label)).toEqual([
      '保留', '复用', '待确认', '回收',
    ])
    w01DemoProjection.coarse_summary.forEach((row) => expect(PATHWAYS).not.toContain(row.label))
    expect(w01DemoProjection.potential.value).toBe('30')
    expect(w01DemoProjection.task_rows).toHaveLength(4)
  })
})
