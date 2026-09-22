import { describe, expect, it } from 'vitest'
import { createTestGraph } from '../test/testGraph'
import { DomainInvariantError } from '../validation'
import { FixtureProjectDataRepository } from './FixtureProjectDataRepository'

describe('FixtureProjectDataRepository', () => {
  it('serves canonical records behind the repository boundary', async () => {
    const repository = new FixtureProjectDataRepository(createTestGraph())
    await expect(repository.getProject('p1')).resolves.toMatchObject({ project_id: 'p1' })
    await expect(repository.getScenes('p1')).resolves.toHaveLength(2)
    await expect(repository.getVerificationItems('p1', 'b1')).resolves.toHaveLength(2)
  })

  it('rejects contradictory fixtures at construction', () => {
    const graph = createTestGraph()
    graph.verificationItems[0].batch_id = 'missing'
    expect(() => new FixtureProjectDataRepository(graph)).toThrow(DomainInvariantError)
  })
})
