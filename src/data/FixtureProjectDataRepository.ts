import type {
  AssessmentBatchId,
  ProjectGraph,
  ProjectId,
} from '../domain'
import { assertValidProjectGraph } from '../validation'
import type { ProjectDataRepository } from './ProjectDataRepository'

/** In-memory adapter for non-authoritative fixtures. Future API adapters use the same interface. */
export class FixtureProjectDataRepository implements ProjectDataRepository {
  constructor(private readonly graph: ProjectGraph) {
    assertValidProjectGraph(graph)
  }

  async getProject(projectId: ProjectId) {
    return this.graph.projects.find((project) => project.project_id === projectId) ?? null
  }

  async getScenes(projectId: ProjectId) {
    return this.graph.scenes.filter((scene) => scene.project_id === projectId)
  }

  async getComponentInstances(projectId: ProjectId) {
    return this.graph.componentInstances.filter((instance) => instance.project_id === projectId)
  }

  async getAssessmentBatches(projectId: ProjectId) {
    return this.graph.assessmentBatches.filter((batch) => batch.project_id === projectId)
  }

  async getVerificationItems(projectId: ProjectId, batchId?: AssessmentBatchId) {
    const batchIds = new Set(
      this.graph.assessmentBatches
        .filter((batch) => batch.project_id === projectId)
        .map((batch) => batch.batch_id),
    )
    return this.graph.verificationItems.filter(
      (item) => batchIds.has(item.batch_id) && (!batchId || item.batch_id === batchId),
    )
  }

  async getEvidenceAssets(projectId: ProjectId, batchId?: AssessmentBatchId) {
    return this.graph.evidenceAssets.filter(
      (asset) => asset.project_id === projectId && (!batchId || asset.batch_id === batchId),
    )
  }

  async getHumanVerifiedFacts(projectId: ProjectId, batchId?: AssessmentBatchId) {
    return this.graph.humanVerifiedFacts.filter(
      (fact) => fact.project_id === projectId && (!batchId || fact.batch_id === batchId),
    )
  }

  async getReferenceSources(projectId: ProjectId, batchId?: AssessmentBatchId) {
    return this.graph.referenceSources.filter(
      (source) =>
        source.project_id === projectId && (!batchId || source.batch_ids?.includes(batchId) === true),
    )
  }

  async getLocalOpportunities(projectId: ProjectId, batchId?: AssessmentBatchId) {
    return this.graph.localOpportunities.filter(
      (opportunity) =>
        opportunity.project_id === projectId &&
        (!batchId || opportunity.batch_ids?.includes(batchId) === true),
    )
  }
}
