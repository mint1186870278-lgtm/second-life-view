import type { AssessmentBatch, ComponentInstance, ProjectId, Scene, VerificationItem } from '../domain'
import {
  getActiveVerificationItemsForProject,
  getProjectAssessmentBatchCount,
  getProjectComponentInstanceCount,
  getProjectSceneCount,
} from './projectSelectors'

export interface CreationAnalysisSummary {
  sceneCount: number
  componentCount: number
  assessmentBatchCount: number
  activeVerificationItemCount: number
  processedScenes: Scene[]
}

export function buildCreationAnalysisSummary(
  projectId: ProjectId,
  scenes: readonly Scene[],
  componentInstances: readonly ComponentInstance[],
  assessmentBatches: readonly AssessmentBatch[],
  verificationItems: readonly VerificationItem[],
): CreationAnalysisSummary {
  return {
    sceneCount: getProjectSceneCount(projectId, scenes),
    componentCount: getProjectComponentInstanceCount(projectId, componentInstances),
    assessmentBatchCount: getProjectAssessmentBatchCount(projectId, assessmentBatches),
    activeVerificationItemCount: getActiveVerificationItemsForProject(projectId, assessmentBatches, verificationItems).length,
    processedScenes: scenes.filter((scene) => scene.project_id === projectId && scene.ingestion_status === 'received'),
  }
}
