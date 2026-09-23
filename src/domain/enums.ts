export const PATHWAYS = [
  'KEEP_IN_PLACE',
  'DIRECT_REUSE',
  'REFURBISH',
  'REPURPOSE',
  'MATERIAL_RECOVERY',
  'DISPOSAL',
] as const
export type Pathway = (typeof PATHWAYS)[number]

export const EVIDENCE_STATUSES = [
  'supported',
  'conditional',
  'insufficient_evidence',
  'not_applicable',
] as const
export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number]

export const REVIEW_STATUSES = ['unreviewed', 'in_review', 'reviewed'] as const
export type ReviewStatus = (typeof REVIEW_STATUSES)[number]

export const VERIFICATION_STATUSES = [
  'unverified',
  'unable_to_verify',
  'verified',
  'not_applicable',
] as const
export type VerificationStatus = (typeof VERIFICATION_STATUSES)[number]

export const VERIFICATION_TYPES = [
  'onsite_observation',
  'document_check',
  'specialist_review',
] as const
export type VerificationType = (typeof VERIFICATION_TYPES)[number]

export const SCENE_INGESTION_STATUSES = [
  'waiting',
  'receiving',
  'received',
  'ingestion_error',
] as const
export type SceneIngestionStatus = (typeof SCENE_INGESTION_STATUSES)[number]
