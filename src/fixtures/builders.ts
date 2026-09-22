import type { Project, ProjectGraph } from '../domain'

export function createEmptyFixtureGraph(project: Project): ProjectGraph {
  return {
    projects: [project],
    scenes: [],
    componentInstances: [],
    assessmentBatches: [],
    verificationItems: [],
    evidenceAssets: [],
    humanVerifiedFacts: [],
    referenceSources: [],
    localOpportunities: [],
    fixtureMetadata: {
      kind: 'demo-fixture',
      authority: 'non-authoritative',
      description: 'Structurally valid Phase 1A fixture. It intentionally contains no invented project inventory.',
    },
  }
}
