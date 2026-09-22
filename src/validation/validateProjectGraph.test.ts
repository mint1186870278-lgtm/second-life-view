import { describe, expect, it } from 'vitest'
import type { ProjectGraph } from '../domain'
import { createTestGraph } from '../test/testGraph'
import { assertValidProjectGraph, DomainInvariantError, validateProjectGraph } from '.'

function codes(graph: ProjectGraph) {
  return validateProjectGraph(graph).issues.map((issue) => issue.code)
}

describe('project graph invariants', () => {
  it('accepts the coherent minimal test graph', () => {
    const result = validateProjectGraph(createTestGraph())
    expect(result).toEqual({ valid: true, issues: [] })
    expect(() => assertValidProjectGraph(createTestGraph())).not.toThrow()
  })

  it('detects duplicate IDs', () => {
    const graph = createTestGraph()
    graph.scenes.push({ ...graph.scenes[0] })
    expect(codes(graph)).toContain('DUPLICATE_ID')
  })

  it('detects missing Project references', () => {
    const graph = createTestGraph()
    graph.scenes[0].project_id = 'missing'
    expect(codes(graph)).toContain('MISSING_PROJECT_REFERENCE')
  })

  it('detects missing Scene and Batch references from ComponentInstances', () => {
    const graph = createTestGraph()
    graph.componentInstances[0].scene_id = 'missing-scene'
    graph.componentInstances[0].batch_id = 'missing-batch'
    const resultCodes = codes(graph)
    expect(resultCodes).toContain('MISSING_SCENE_REFERENCE')
    expect(resultCodes).toContain('MISSING_BATCH_REFERENCE')
  })

  it('detects a VerificationItem pointing to a missing Batch', () => {
    const graph = createTestGraph()
    graph.verificationItems[0].batch_id = 'missing-batch'
    expect(codes(graph)).toContain('MISSING_BATCH_REFERENCE')
  })

  it('detects Batch/Component Scene mismatch', () => {
    const graph = createTestGraph()
    graph.componentInstances[0].scene_id = 's2'
    expect(codes(graph)).toContain('BATCH_SCENE_MISMATCH')
  })

  it('detects denormalized Batch quantity drift', () => {
    const graph = createTestGraph()
    graph.assessmentBatches[0].denormalized_quantity = 99
    expect(codes(graph)).toContain('BATCH_QUANTITY_DRIFT')
  })

  it('detects cached W02-A pending count drift', () => {
    const graph = createTestGraph()
    graph.assessmentBatches[0].denormalized_pending_verification_count = 99
    expect(codes(graph)).toContain('BATCH_PENDING_COUNT_DRIFT')
  })

  it('detects invalid runtime enum values', () => {
    const graph = createTestGraph()
    graph.assessmentBatches[0].pathway = 'INVENTED' as never
    graph.scenes[0].ingestion_status = 'invented' as never
    graph.verificationItems[0].status = 'invented' as never
    expect(codes(graph).filter((code) => code === 'INVALID_ENUM_VALUE')).toHaveLength(3)
  })

  it('throws loudly instead of repairing contradictory data', () => {
    const graph = createTestGraph()
    graph.assessmentBatches[0].denormalized_quantity = 99
    expect(() => assertValidProjectGraph(graph)).toThrow(DomainInvariantError)
  })
})
