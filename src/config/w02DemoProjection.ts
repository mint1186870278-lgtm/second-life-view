import type {
  EvidenceStatus,
  Pathway,
  ReviewStatus,
  VerificationStatus,
  VerificationType,
} from '../domain'

/**
 * Visual-density fixtures copied from the accepted W02 prototype.
 * These rows are presentation-only: they are never passed to domain selectors,
 * never become ProjectSession truth, and never provide a D01 navigation target.
 */
export interface W02DemoBatchRow {
  presentation_batch_id: string
  material_group: string
  component_type: string
  batch_label: string
  quantity: number
  scene_key: string
  scene_name: string
  scene_index: number
  pathway: Pathway
  evidence_status: EvidenceStatus
  review_status: ReviewStatus
  pending_verification_count: number
  attention: boolean
  attention_reason?: string
}

export interface W02DemoVerificationRow {
  presentation_verification_id: string
  presentation_batch_id: string
  material_group: string
  batch_label: string
  scene_key: string
  scene_name: string
  scene_index: number
  field: string
  question: string
  verification_type: VerificationType
  status: VerificationStatus
  discovered_at: string
  discovered_source: string
}

const batchRows: readonly W02DemoBatchRow[] = [
  {
    presentation_batch_id: 'demo-wood-deck-a', material_group: '木材', component_type: '户外地板',
    batch_label: '户外地板 · A组', quantity: 1, scene_key: 'demo-scene-entry', scene_name: '入口',
    scene_index: 3, pathway: 'KEEP_IN_PLACE', evidence_status: 'insufficient_evidence',
    review_status: 'unreviewed', pending_verification_count: 1, attention: true,
    attention_reason: '当前证据不足',
  },
  {
    presentation_batch_id: 'demo-wood-planter-a', material_group: '木材', component_type: '木质花箱',
    batch_label: '木质花箱 · A组', quantity: 1, scene_key: 'demo-scene-lounge', scene_name: '休息区',
    scene_index: 2, pathway: 'REPURPOSE', evidence_status: 'conditional',
    review_status: 'in_review', pending_verification_count: 1, attention: false,
  },
  {
    presentation_batch_id: 'demo-metal-railing-b', material_group: '金属', component_type: '栏杆',
    batch_label: '栏杆 · B组', quantity: 1, scene_key: 'demo-scene-lounge', scene_name: '休息区',
    scene_index: 2, pathway: 'MATERIAL_RECOVERY', evidence_status: 'conditional',
    review_status: 'in_review', pending_verification_count: 1, attention: true,
    attention_reason: '本地机会尚未确认',
  },
  {
    presentation_batch_id: 'demo-glass-a', material_group: '玻璃', component_type: '玻璃构件',
    batch_label: '玻璃构件 · A组', quantity: 1, scene_key: 'demo-scene-office', scene_name: '办公区',
    scene_index: 4, pathway: 'DIRECT_REUSE', evidence_status: 'supported',
    review_status: 'reviewed', pending_verification_count: 0, attention: false,
  },
  {
    presentation_batch_id: 'demo-glass-b', material_group: '玻璃', component_type: '玻璃构件',
    batch_label: '玻璃构件 · B组', quantity: 1, scene_key: 'demo-scene-office', scene_name: '办公区',
    scene_index: 4, pathway: 'REPURPOSE', evidence_status: 'conditional',
    review_status: 'unreviewed', pending_verification_count: 0, attention: false,
  },
  {
    presentation_batch_id: 'demo-concrete-a', material_group: '混凝土', component_type: '混凝土构件',
    batch_label: '混凝土构件 · A组', quantity: 1, scene_key: 'demo-scene-service', scene_name: '后勤区',
    scene_index: 5, pathway: 'MATERIAL_RECOVERY', evidence_status: 'not_applicable',
    review_status: 'reviewed', pending_verification_count: 0, attention: false,
  },
  {
    presentation_batch_id: 'demo-planting-a', material_group: '植栽', component_type: '花池',
    batch_label: '花池 · A组', quantity: 8, scene_key: 'demo-scene-roof', scene_name: '屋顶花园',
    scene_index: 1, pathway: 'KEEP_IN_PLACE', evidence_status: 'supported',
    review_status: 'reviewed', pending_verification_count: 0, attention: false,
  },
  {
    presentation_batch_id: 'demo-planting-b', material_group: '植栽', component_type: '花池',
    batch_label: '花池 · B组', quantity: 1, scene_key: 'demo-scene-roof', scene_name: '屋顶花园',
    scene_index: 1, pathway: 'KEEP_IN_PLACE', evidence_status: 'conditional',
    review_status: 'in_review', pending_verification_count: 0, attention: false,
  },
  {
    presentation_batch_id: 'demo-other-a', material_group: '其他', component_type: '其他构件',
    batch_label: '其他构件 · A组', quantity: 1, scene_key: 'demo-scene-service', scene_name: '后勤区',
    scene_index: 5, pathway: 'DISPOSAL', evidence_status: 'insufficient_evidence',
    review_status: 'unreviewed', pending_verification_count: 1, attention: true,
    attention_reason: '分组与证据需要复核',
  },
]

const verificationRows: readonly W02DemoVerificationRow[] = [
  {
    presentation_verification_id: 'demo-v-surface', presentation_batch_id: 'demo-wood-deck-a',
    material_group: '木材', batch_label: '户外地板 · A组', scene_key: 'demo-scene-entry',
    scene_name: '入口', scene_index: 3, field: '表面处理', question: '确认是否有涂层 / 防腐处理',
    verification_type: 'onsite_observation', status: 'unverified',
    discovered_at: '2026.09.22', discovered_source: '现场采集',
  },
  {
    presentation_verification_id: 'demo-v-size', presentation_batch_id: 'demo-wood-deck-a',
    material_group: '木材', batch_label: '户外地板 · A组', scene_key: 'demo-scene-entry',
    scene_name: '入口', scene_index: 3, field: '现状尺寸', question: '补充关键尺寸与拆卸余量',
    verification_type: 'onsite_observation', status: 'unable_to_verify',
    discovered_at: '2026.09.22', discovered_source: '现场采集',
  },
  {
    presentation_verification_id: 'demo-v-source', presentation_batch_id: 'demo-wood-planter-a',
    material_group: '木材', batch_label: '木质花箱 · A组', scene_key: 'demo-scene-lounge',
    scene_name: '休息区', scene_index: 2, field: '构件来源', question: '核对现有记录中的材料来源信息',
    verification_type: 'document_check', status: 'unverified',
    discovered_at: '2026.09.21', discovered_source: '文件审查',
  },
  {
    presentation_verification_id: 'demo-v-connection', presentation_batch_id: 'demo-metal-railing-b',
    material_group: '金属', batch_label: '栏杆 · B组', scene_key: 'demo-scene-lounge',
    scene_name: '休息区', scene_index: 2, field: '连接状态', question: '确认栏杆连接节点是否完整',
    verification_type: 'onsite_observation', status: 'unverified',
    discovered_at: '2026.09.22', discovered_source: '现场采集',
  },
  {
    presentation_verification_id: 'demo-v-recovery', presentation_batch_id: 'demo-other-a',
    material_group: '其他', batch_label: '其他构件 · A组', scene_key: 'demo-scene-service',
    scene_name: '后勤区', scene_index: 5, field: '回收条件', question: '确认材料回收前处理要求',
    verification_type: 'specialist_review', status: 'unable_to_verify',
    discovered_at: '2026.09.20', discovered_source: '人工审查',
  },
  {
    presentation_verification_id: 'demo-v-verified', presentation_batch_id: 'demo-metal-railing-b',
    material_group: '金属', batch_label: '栏杆 · A组', scene_key: 'demo-scene-entry',
    scene_name: '入口', scene_index: 3, field: '固定方式', question: '已确认连接件可拆卸',
    verification_type: 'onsite_observation', status: 'verified',
    discovered_at: '2026.09.21', discovered_source: '人工审查',
  },
  {
    presentation_verification_id: 'demo-v-na', presentation_batch_id: 'demo-planting-a',
    material_group: '植栽', batch_label: '花池 · A组', scene_key: 'demo-scene-roof',
    scene_name: '屋顶花园', scene_index: 1, field: '构件来源', question: '该项不适用于现有植栽分组',
    verification_type: 'document_check', status: 'not_applicable',
    discovered_at: '2026.09.19', discovered_source: '文件审查',
  },
]

export const w02DemoProjection = {
  batch_rows: batchRows,
  verification_rows: verificationRows,
  review_date: '2026.09.22',
} as const
