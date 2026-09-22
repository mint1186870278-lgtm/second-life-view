import type {
  EvidenceStatus,
  Pathway,
  ReviewStatus,
  SceneIngestionStatus,
  VerificationStatus,
  VerificationType,
} from './enums'
import type {
  AssessmentBatchId,
  ComponentInstanceId,
  EvidenceAssetId,
  HumanVerifiedFactId,
  LocalOpportunityId,
  ProjectId,
  ReferenceSourceId,
  SceneId,
  VerificationItemId,
} from './ids'

export interface Project {
  project_id: ProjectId
  name: string
  region: string
  project_type: string
  project_stage: string
  description?: string
}

export interface Scene {
  scene_id: SceneId
  project_id: ProjectId
  name: string
  ingestion_status: SceneIngestionStatus
}

export interface ComponentInstance {
  component_instance_id: ComponentInstanceId
  project_id: ProjectId
  scene_id: SceneId
  batch_id?: AssessmentBatchId
}

export interface AssessmentBatch {
  batch_id: AssessmentBatchId
  project_id: ProjectId
  scene_id: SceneId
  material_group: string
  component_type: string
  batch_label: string
  pathway: Pathway
  evidence_status: EvidenceStatus
  review_status: ReviewStatus
  attention: boolean
  attention_reason?: string

  /** Optional transport cache only; validation rejects drift from canonical instances. */
  denormalized_quantity?: number
  /** Optional transport cache only; validation rejects drift from VerificationItems. */
  denormalized_pending_verification_count?: number
}

export interface VerificationItem {
  verification_id: VerificationItemId
  batch_id: AssessmentBatchId
  field: string
  question: string
  verification_type: VerificationType
  status: VerificationStatus
  focus_key?: string
  discovered_at?: string
  /** Intentionally open: the production discovered-source taxonomy is not frozen. */
  discovered_source?: string
}

export interface EvidenceAsset {
  evidence_asset_id: EvidenceAssetId
  project_id: ProjectId
  batch_id: AssessmentBatchId
  scene_id?: SceneId
  component_instance_id?: ComponentInstanceId
  label?: string
}

export interface HumanVerifiedFact {
  human_verified_fact_id: HumanVerifiedFactId
  project_id: ProjectId
  batch_id: AssessmentBatchId
  component_instance_id: ComponentInstanceId
  verification_id?: VerificationItemId
  field_key: string
  value: unknown
  note?: string
  verified_at?: string
}

export interface ReferenceSource {
  reference_source_id: ReferenceSourceId
  project_id: ProjectId
  batch_ids?: AssessmentBatchId[]
  title: string
}

export interface LocalOpportunity {
  local_opportunity_id: LocalOpportunityId
  project_id: ProjectId
  batch_ids?: AssessmentBatchId[]
  name: string
}
