import type {
  AssessmentBatch,
  AssessmentBatchId,
  ComponentInstance,
  EvidenceAsset,
  HumanVerifiedFact,
  LocalOpportunity,
  Project,
  ProjectId,
  ReferenceSource,
  Scene,
  VerificationItem,
} from '../domain'

export interface ProjectDataRepository {
  getProject(projectId: ProjectId): Promise<Project | null>
  getScenes(projectId: ProjectId): Promise<readonly Scene[]>
  getComponentInstances(projectId: ProjectId): Promise<readonly ComponentInstance[]>
  getAssessmentBatches(projectId: ProjectId): Promise<readonly AssessmentBatch[]>
  getVerificationItems(projectId: ProjectId, batchId?: AssessmentBatchId): Promise<readonly VerificationItem[]>
  getEvidenceAssets(projectId: ProjectId, batchId?: AssessmentBatchId): Promise<readonly EvidenceAsset[]>
  getHumanVerifiedFacts(projectId: ProjectId, batchId?: AssessmentBatchId): Promise<readonly HumanVerifiedFact[]>
  getReferenceSources(projectId: ProjectId, batchId?: AssessmentBatchId): Promise<readonly ReferenceSource[]>
  getLocalOpportunities(projectId: ProjectId, batchId?: AssessmentBatchId): Promise<readonly LocalOpportunity[]>
}
