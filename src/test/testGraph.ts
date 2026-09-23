import type { ProjectGraph } from '../domain'

/** Small architecture-test graph only. It is not the product demo dataset. */
export function createTestGraph(): ProjectGraph {
  return {
    projects: [
      { project_id: 'p1', name: 'Test Project', region: '', project_type: '', project_stage: '' },
    ],
    scenes: [
      { scene_id: 's1', project_id: 'p1', name: 'Scene 1', ingestion_status: 'received' },
      { scene_id: 's2', project_id: 'p1', name: 'Scene 2', ingestion_status: 'received' },
    ],
    componentInstances: [
      { component_instance_id: 'c1', project_id: 'p1', scene_id: 's1', batch_id: 'b1' },
      { component_instance_id: 'c2', project_id: 'p1', scene_id: 's1', batch_id: 'b1' },
      { component_instance_id: 'c3', project_id: 'p1', scene_id: 's2', batch_id: 'b2' },
    ],
    assessmentBatches: [
      {
        batch_id: 'b1', project_id: 'p1', scene_id: 's1', material_group: 'Wood',
        component_type: 'Fence', batch_label: 'Fence A', pathway: 'REFURBISH',
        evidence_status: 'conditional', review_status: 'unreviewed', attention: true,
        denormalized_quantity: 2, denormalized_pending_verification_count: 2,
      },
      {
        batch_id: 'b2', project_id: 'p1', scene_id: 's2', material_group: 'Metal',
        component_type: 'Railing', batch_label: 'Railing A', pathway: 'KEEP_IN_PLACE',
        evidence_status: 'supported', review_status: 'reviewed', attention: false,
        denormalized_quantity: 1, denormalized_pending_verification_count: 0,
      },
    ],
    verificationItems: [
      { verification_id: 'v1', batch_id: 'b1', field: 'A', question: 'A?', verification_type: 'onsite_observation', status: 'unverified' },
      { verification_id: 'v2', batch_id: 'b1', field: 'B', question: 'B?', verification_type: 'specialist_review', status: 'unable_to_verify' },
      { verification_id: 'v3', batch_id: 'b2', field: 'C', question: 'C?', verification_type: 'document_check', status: 'verified' },
      { verification_id: 'v4', batch_id: 'b2', field: 'D', question: 'D?', verification_type: 'document_check', status: 'not_applicable' },
    ],
    evidenceAssets: [],
    humanVerifiedFacts: [],
    referenceSources: [],
    localOpportunities: [],
    fixtureMetadata: {
      kind: 'demo-fixture', authority: 'non-authoritative',
      description: 'Minimal test graph; never use as the product fixture.',
    },
  }
}
