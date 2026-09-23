import type { ProjectGraph } from '../domain'

/**
 * Non-authoritative Phase 1B visual-flow fixture. This deliberately small,
 * coherent graph is not the final canonical demo dataset.
 */
export const CREATION_DEMO_PROJECT_ID = 'fixture-project-creation'

export const creationDemoGraph: ProjectGraph = {
  projects: [{
    project_id: CREATION_DEMO_PROJECT_ID,
    name: 'HSBC MKK',
    region: '南京 · 江苏',
    project_type: '改造 / 翻新',
    project_stage: '拟拆改前评估',
    description: '对现有构件进行 360° 审计，识别可能被保留、复用或再生的构件，为后续改造与资源循环提供依据。',
  }],
  scenes: [
    { scene_id: 'fixture-scene-roof', project_id: CREATION_DEMO_PROJECT_ID, name: '屋顶花园', ingestion_status: 'received' },
    { scene_id: 'fixture-scene-lounge', project_id: CREATION_DEMO_PROJECT_ID, name: '休息区', ingestion_status: 'received' },
    { scene_id: 'fixture-scene-entry', project_id: CREATION_DEMO_PROJECT_ID, name: '入口', ingestion_status: 'received' },
    { scene_id: 'fixture-scene-service', project_id: CREATION_DEMO_PROJECT_ID, name: '办公区', ingestion_status: 'received' },
  ],
  componentInstances: [
    { component_instance_id: 'fixture-component-01', project_id: CREATION_DEMO_PROJECT_ID, scene_id: 'fixture-scene-roof', batch_id: 'fixture-batch-wood' },
    { component_instance_id: 'fixture-component-02', project_id: CREATION_DEMO_PROJECT_ID, scene_id: 'fixture-scene-roof', batch_id: 'fixture-batch-wood' },
    { component_instance_id: 'fixture-component-03', project_id: CREATION_DEMO_PROJECT_ID, scene_id: 'fixture-scene-lounge', batch_id: 'fixture-batch-metal' },
    { component_instance_id: 'fixture-component-04', project_id: CREATION_DEMO_PROJECT_ID, scene_id: 'fixture-scene-lounge', batch_id: 'fixture-batch-metal' },
  ],
  assessmentBatches: [
    {
      batch_id: 'fixture-batch-wood', project_id: CREATION_DEMO_PROJECT_ID,
      scene_id: 'fixture-scene-roof', material_group: '木材', component_type: '固定柜体',
      batch_label: '木质固定柜体', pathway: 'REFURBISH', evidence_status: 'conditional',
      review_status: 'unreviewed', attention: true, attention_reason: '需要现场确认隐藏连接方式',
    },
    {
      batch_id: 'fixture-batch-metal', project_id: CREATION_DEMO_PROJECT_ID,
      scene_id: 'fixture-scene-lounge', material_group: '金属', component_type: '栏杆',
      batch_label: '金属栏杆', pathway: 'KEEP_IN_PLACE', evidence_status: 'supported',
      review_status: 'reviewed', attention: false,
    },
  ],
  verificationItems: [
    {
      verification_id: 'fixture-verification-01', batch_id: 'fixture-batch-wood', field: '固定方式',
      question: '确认柜体与墙面的固定方式', verification_type: 'onsite_observation', status: 'unverified',
      focus_key: 'fixing_method',
    },
    {
      verification_id: 'fixture-verification-02', batch_id: 'fixture-batch-wood', field: '隐藏腐朽',
      question: '确认背板后方是否存在隐藏腐朽', verification_type: 'specialist_review', status: 'unable_to_verify',
      focus_key: 'hidden_damage',
    },
  ],
  evidenceAssets: [],
  humanVerifiedFacts: [],
  referenceSources: [],
  localOpportunities: [],
  fixtureMetadata: {
    kind: 'demo-fixture',
    authority: 'non-authoritative',
    description: 'Phase 1B visual-flow fixture only. Counts and records are not the final canonical demo inventory.',
  },
}
