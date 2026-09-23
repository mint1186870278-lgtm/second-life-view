import type {
  AssessmentBatch,
  ComponentInstance,
  EvidenceAsset,
  HumanVerifiedFact,
  LocalOpportunity,
  Project,
  ReferenceSource,
  Scene,
  VerificationItem,
} from './entities'

export interface FixtureMetadata {
  kind: 'demo-fixture'
  authority: 'non-authoritative'
  description: string
}

export interface ProjectGraph {
  projects: Project[]
  scenes: Scene[]
  componentInstances: ComponentInstance[]
  assessmentBatches: AssessmentBatch[]
  verificationItems: VerificationItem[]
  evidenceAssets: EvidenceAsset[]
  humanVerifiedFacts: HumanVerifiedFact[]
  referenceSources: ReferenceSource[]
  localOpportunities: LocalOpportunity[]
  fixtureMetadata?: FixtureMetadata
}
