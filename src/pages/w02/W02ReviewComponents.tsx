import {
  Anchor,
  Box,
  Camera,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  FileText,
  Info,
  Layers3,
  Leaf,
  MapPin,
  Recycle,
  RefreshCw,
  Search,
  Trash2,
  TriangleAlert,
  UserRound,
  type LucideIcon,
} from 'lucide-react'
import type {
  AssessmentBatchId,
  EvidenceStatus,
  Pathway,
  ReviewStatus,
  VerificationStatus,
  VerificationType,
} from '../../domain'
import type { W02ASummaryReadModel, W02BSummaryReadModel } from '../../selectors'

export type W02Tab = 'draft' | 'verification'

export interface W02DraftFilters {
  material: string
  scene: string
  evidence: EvidenceStatus | 'all'
  review: ReviewStatus | 'all'
  search: string
}

export interface W02VerificationFilters {
  material: string
  scene: string
  type: VerificationType | 'all'
  status: VerificationStatus | 'active' | 'all'
  search: string
}

export interface W02DraftDisplayRow {
  row_key: string
  canonical_batch_id?: AssessmentBatchId
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

export interface W02VerificationDisplayRow {
  row_key: string
  group_key: string
  canonical_batch_id?: AssessmentBatchId
  material_group: string
  batch_label: string
  scene_key: string
  scene_name: string
  scene_index: number
  field: string
  question: string
  verification_type: VerificationType
  status: VerificationStatus
  focus_target?: string
  discovered_at?: string
  discovered_source?: string
}

export interface W02AttentionRow {
  row_key: string
  canonical_batch_id?: AssessmentBatchId
  batch_label: string
  material_group: string
  attention_reason: string
}

interface Option {
  value: string
  label: string
}

const PATHWAY_LABELS: Record<Pathway, string> = {
  KEEP_IN_PLACE: '原位保留',
  DIRECT_REUSE: '直接复用',
  REFURBISH: '修复翻新',
  REPURPOSE: '改造再利用',
  MATERIAL_RECOVERY: '材料回收',
  DISPOSAL: '处置',
}

const PATHWAY_ICONS: Record<Pathway, { icon: LucideIcon; tone: string }> = {
  KEEP_IN_PLACE: { icon: Anchor, tone: 'keep' },
  DIRECT_REUSE: { icon: RefreshCw, tone: 'reuse' },
  REFURBISH: { icon: Leaf, tone: 'refurbish' },
  REPURPOSE: { icon: Layers3, tone: 'repurpose' },
  MATERIAL_RECOVERY: { icon: Recycle, tone: 'recovery' },
  DISPOSAL: { icon: Trash2, tone: 'disposal' },
}

const EVIDENCE_LABELS: Record<EvidenceStatus, string> = {
  supported: '有依据',
  conditional: '条件性',
  insufficient_evidence: '证据不足',
  not_applicable: '不适用',
}

const REVIEW_LABELS: Record<ReviewStatus, string> = {
  unreviewed: '未审查',
  in_review: '审查中',
  reviewed: '已审查',
}

const VERIFICATION_LABELS: Record<VerificationStatus, string> = {
  unverified: '待核实',
  unable_to_verify: '无法现场确认',
  verified: '已核实',
  not_applicable: '不适用',
}

export function W02ReviewTabs({
  tab,
  onChange,
}: {
  tab: W02Tab
  onChange: (tab: W02Tab) => void
}) {
  return (
    <div className="w02-tabs" role="tablist" aria-label="项目审查视图">
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'draft'}
        className={tab === 'draft' ? 'active' : ''}
        onClick={() => onChange('draft')}
      >
        评估草案
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'verification'}
        className={tab === 'verification' ? 'active' : ''}
        onClick={() => onChange('verification')}
      >
        待核实
      </button>
    </div>
  )
}

function SummaryCard({
  label,
  value,
  unit,
  icon: Icon,
  tone = '',
  active = false,
  onClick,
}: {
  label: string
  value: number
  unit: string
  icon: LucideIcon
  tone?: string
  active?: boolean
  onClick?: () => void
}) {
  const content = (
    <>
      <span className="w02-stat-icon"><Icon size={23} /></span>
      <span className="w02-stat-copy">
        <span>{label}</span>
        <span className="w02-stat-metric"><strong>{value}</strong><small>{unit}</small></span>
      </span>
    </>
  )
  const className = `w02-stat-card ${tone} ${active ? 'active' : ''} ${onClick ? '' : 'display-only'}`.trim()
  return onClick ? (
    <button type="button" className={className} data-summary-card={label} aria-pressed={active} onClick={onClick}>
      {content}
    </button>
  ) : (
    <div className={className} data-summary-card={label}>{content}</div>
  )
}

export function W02DraftSummary({
  summary,
  activeFilter,
  onFilter,
}: {
  summary: W02ASummaryReadModel
  activeFilter: 'all' | 'reviewed' | 'attention'
  onFilter: (filter: 'all' | 'reviewed' | 'attention') => void
}) {
  return (
    <div className="w02-summary-grid w02-draft-summary-grid" aria-label="评估草案概览">
      <SummaryCard label="评估分组" value={summary.assessment_batch_count} unit="个分组" icon={Box} active={activeFilter === 'all'} onClick={() => onFilter('all')} />
      <SummaryCard label="已审查" value={summary.reviewed_batch_count} unit="个分组" icon={CheckCircle2} tone="success" active={activeFilter === 'reviewed'} onClick={() => onFilter(activeFilter === 'reviewed' ? 'all' : 'reviewed')} />
      <SummaryCard label="需关注" value={summary.attention_batch_count} unit="个分组" icon={TriangleAlert} tone="attention" active={activeFilter === 'attention'} onClick={() => onFilter(activeFilter === 'attention' ? 'all' : 'attention')} />
      <SummaryCard label="场景" value={summary.scene_count} unit="个场景" icon={MapPin} />
    </div>
  )
}

export function W02VerificationSummary({ summary }: { summary: W02BSummaryReadModel }) {
  return (
    <div className="w02-summary-grid w02-v-summary-grid" aria-label="待核实概览">
      <SummaryCard label="待核实事项" value={summary.verification_item_count} unit="项" icon={CircleHelp} tone="warning" />
      <SummaryCard label="涉及评估分组" value={summary.affected_batch_count} unit="个" icon={Box} />
      <SummaryCard label="现场观察" value={summary.onsite_observation} unit="项" icon={Camera} />
      <SummaryCard label="文件核对" value={summary.document_check} unit="项" icon={FileText} />
      <SummaryCard label="专业复核" value={summary.specialist_review} unit="项" icon={UserRound} />
    </div>
  )
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: readonly Option[]
  onChange: (value: string) => void
}) {
  return (
    <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
      {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
    </select>
  )
}

export function W02DraftToolbar({
  filters,
  materials,
  scenes,
  onChange,
}: {
  filters: W02DraftFilters
  materials: readonly Option[]
  scenes: readonly Option[]
  onChange: (next: W02DraftFilters) => void
}) {
  return (
    <div className="w02-toolbar">
      <FilterSelect label="材料筛选" value={filters.material} options={materials} onChange={(material) => onChange({ ...filters, material })} />
      <FilterSelect label="场景筛选" value={filters.scene} options={scenes} onChange={(scene) => onChange({ ...filters, scene })} />
      <FilterSelect label="证据状态筛选" value={filters.evidence} options={[
        { value: 'all', label: '全部证据状态' }, { value: 'supported', label: '有依据' },
        { value: 'conditional', label: '条件性' }, { value: 'insufficient_evidence', label: '证据不足' },
        { value: 'not_applicable', label: '不适用' },
      ]} onChange={(evidence) => onChange({ ...filters, evidence: evidence as W02DraftFilters['evidence'] })} />
      <FilterSelect label="审查状态筛选" value={filters.review} options={[
        { value: 'all', label: '全部审查状态' }, { value: 'unreviewed', label: '未审查' },
        { value: 'in_review', label: '审查中' }, { value: 'reviewed', label: '已审查' },
      ]} onChange={(review) => onChange({ ...filters, review: review as W02DraftFilters['review'] })} />
      <label className="w02-search"><Search size={18} /><input aria-label="搜索评估分组" value={filters.search} placeholder="搜索构件 / 分组 / 场景" onChange={(event) => onChange({ ...filters, search: event.target.value })} /></label>
    </div>
  )
}

export function W02VerificationToolbar({
  filters,
  materials,
  scenes,
  onChange,
}: {
  filters: W02VerificationFilters
  materials: readonly Option[]
  scenes: readonly Option[]
  onChange: (next: W02VerificationFilters) => void
}) {
  return (
    <div className="w02-toolbar verification">
      <FilterSelect label="材料筛选" value={filters.material} options={materials} onChange={(material) => onChange({ ...filters, material })} />
      <FilterSelect label="场景筛选" value={filters.scene} options={scenes} onChange={(scene) => onChange({ ...filters, scene })} />
      <FilterSelect label="核实类型筛选" value={filters.type} options={[
        { value: 'all', label: '全部核实类型' }, { value: 'onsite_observation', label: '现场观察' },
        { value: 'document_check', label: '文件核对' }, { value: 'specialist_review', label: '专业复核' },
      ]} onChange={(type) => onChange({ ...filters, type: type as W02VerificationFilters['type'] })} />
      <FilterSelect label="状态筛选" value={filters.status} options={[
        { value: 'active', label: '待处理状态' }, { value: 'all', label: '全部状态' },
        { value: 'unverified', label: '待核实' }, { value: 'unable_to_verify', label: '无法现场确认' },
        { value: 'verified', label: '已核实' }, { value: 'not_applicable', label: '不适用' },
      ]} onChange={(status) => onChange({ ...filters, status: status as W02VerificationFilters['status'] })} />
      <label className="w02-search"><Search size={18} /><input aria-label="搜索待核实事项" value={filters.search} placeholder="搜索分组 / 核实事项 / 说明 / 场景" onChange={(event) => onChange({ ...filters, search: event.target.value })} /></label>
    </div>
  )
}

function materialTone(material: string) {
  return ({ 木材: 'wood', 金属: 'metal', 玻璃: 'glass', 混凝土: 'concrete', 植栽: 'planting', 其他: 'other' } as Record<string, string>)[material] ?? 'other'
}

function BatchThumb({ material }: { material: string }) {
  return <span className={`w02-thumb ${materialTone(material)}`} aria-hidden="true" />
}

function BatchIdentity({
  row,
  onOpen,
  compact = false,
}: {
  row: Pick<W02DraftDisplayRow, 'canonical_batch_id' | 'batch_label' | 'material_group' | 'scene_index' | 'scene_name'>
  onOpen: (batchId: AssessmentBatchId) => void
  compact?: boolean
}) {
  const content = (
    <>
      <BatchThumb material={row.material_group} />
      <span><strong>{row.batch_label}</strong><small>Scene{String(row.scene_index).padStart(2, '0')} · {row.scene_name}</small></span>
    </>
  )
  const className = compact ? 'w02-v-row-batch' : 'w02-batch-identity'
  return row.canonical_batch_id ? (
    <button type="button" className={className} onClick={() => onOpen(row.canonical_batch_id!)}>{content}</button>
  ) : (
    <div className={`${className} is-static`}>{content}</div>
  )
}

function PathwayCell({ pathway }: { pathway: Pathway }) {
  const { icon: Icon, tone } = PATHWAY_ICONS[pathway]
  return <span className={`w02-pathway ${tone}`}><Icon className="w02-path-icon" /><span>{PATHWAY_LABELS[pathway]}</span></span>
}

function StatusPill({ kind, value }: { kind: 'evidence' | 'review'; value: EvidenceStatus | ReviewStatus }) {
  const label = kind === 'evidence' ? EVIDENCE_LABELS[value as EvidenceStatus] : REVIEW_LABELS[value as ReviewStatus]
  return <span className={`w02-pill ${kind}-${value}`}><span />{label}</span>
}

export function W02DraftTable({
  rows,
  total,
  page,
  pageCount,
  onPage,
  onOpenBatch,
  onClear,
}: {
  rows: readonly W02DraftDisplayRow[]
  total: number
  page: number
  pageCount: number
  onPage: (page: number) => void
  onOpenBatch: (batchId: AssessmentBatchId, focus?: string) => void
  onClear: () => void
}) {
  const materials = [...new Set(rows.map((row) => row.material_group))]
  return (
    <>
      <div className="w02-table-shell">
        {rows.length ? materials.map((material) => {
          const materialRows = rows.filter((row) => row.material_group === material)
          return (
            <section className="w02-material-section" key={material} data-material-section={material}>
              <div className="w02-material-head"><strong>{material}</strong><span>{materialRows.length}个分组</span></div>
              <div className="w02-table-head">
                <span>构件 / 分组</span><span>数量</span><span>当前路径</span><span>证据状态</span><span className="w02-center-col">待核实</span><span>审查状态</span><span>操作</span>
              </div>
              {materialRows.map((row) => (
                <div className="w02-batch-row" key={row.row_key}>
                  <BatchIdentity row={row} onOpen={(batchId) => onOpenBatch(batchId)} />
                  <span className="w02-quantity">{row.quantity}件</span>
                  <PathwayCell pathway={row.pathway} />
                  <StatusPill kind="evidence" value={row.evidence_status} />
                  {row.pending_verification_count > 0 && row.canonical_batch_id ? (
                    <button type="button" className="w02-verification-count" onClick={() => onOpenBatch(row.canonical_batch_id!, 'human_verification')}>{row.pending_verification_count}项</button>
                  ) : (
                    <span className={`w02-verification-count ${row.pending_verification_count === 0 ? 'zero' : 'is-static'}`}>{row.pending_verification_count}项</span>
                  )}
                  <StatusPill kind="review" value={row.review_status} />
                  <span className="w02-360-btn">打开360°</span>
                </div>
              ))}
            </section>
          )
        }) : <div className="w02-empty"><strong>没有符合当前筛选条件的评估分组</strong><button type="button" onClick={onClear}>清除筛选</button></div>}
      </div>
      <div className="w02-table-footer">
        <span>共 {total} 个分组</span>
        {pageCount > 1 && (
          <div className="w02-pagination" aria-label="评估草案分页">
            <button type="button" disabled={page === 1} onClick={() => onPage(page - 1)}>‹</button>
            {Array.from({ length: pageCount }, (_, index) => index + 1).map((pageNumber) => (
              <button type="button" key={pageNumber} className={page === pageNumber ? 'active' : ''} aria-current={page === pageNumber ? 'page' : undefined} onClick={() => onPage(pageNumber)}>{pageNumber}</button>
            ))}
            <button type="button" disabled={page === pageCount} onClick={() => onPage(page + 1)}>›</button>
          </div>
        )}
      </div>
    </>
  )
}

export function W02AttentionRail({
  rows,
  mode,
  onOpen,
}: {
  rows: readonly W02AttentionRow[]
  mode: W02Tab
  onOpen: (batchId: AssessmentBatchId) => void
}) {
  return (
    <aside className="w02-attention-rail">
      <section className="w02-attention-panel">
        <div className="w02-attention-head"><strong>需要关注</strong><span>{rows.length}</span></div>
        <div className="w02-attention-list">
          {rows.length ? rows.slice(0, 4).map((row, index) => {
            const content = (
              <>
                <span className="w02-rank">{index + 1}</span><BatchThumb material={row.material_group} />
                <span className="w02-attention-copy"><strong>{row.batch_label}</strong><small>{row.attention_reason}</small></span>
                <ChevronRight size={16} />
              </>
            )
            return row.canonical_batch_id ? (
              <button type="button" className="w02-attention-item" key={row.row_key} onClick={() => onOpen(row.canonical_batch_id!)}>{content}</button>
            ) : <div className="w02-attention-item is-static" key={row.row_key}>{content}</div>
          }) : <div className="w02-attention-empty">当前没有需要优先处理的分组</div>}
        </div>
      </section>
      <section className="w02-info-callout"><Info size={18} /><p>{mode === 'verification' ? '这里汇总与当前待核实任务相关、需要优先处理的评估分组。' : '这是基于当前审查进度的优先处理清单，帮助您聚焦需要关注的分组。'}</p></section>
    </aside>
  )
}

function VerificationStatusPill({ status }: { status: VerificationStatus }) {
  return <span className={`w02-v-status ${status}`}>{VERIFICATION_LABELS[status]}</span>
}

export interface W02MaterialGroup {
  material: string
  rows: W02VerificationDisplayRow[]
  activeCount: number
  affectedBatchCount: number
}

export function W02VerificationTable({
  groups,
  expandedMaterial,
  onToggle,
  onOpenBatch,
  onClear,
}: {
  groups: readonly W02MaterialGroup[]
  expandedMaterial: string | null
  onToggle: (material: string) => void
  onOpenBatch: (batchId: AssessmentBatchId, focus?: string) => void
  onClear: () => void
}) {
  return (
    <>
      <div className="w02-v-global-head" data-global-verification-header>
        <span>构件 / 分组</span><span>待核实事项</span><span>相关说明</span><span>状态</span><span>发现于</span><span>操作</span>
      </div>
      <div className="w02-v-accordion">
        {groups.length ? groups.map((group) => {
          const expanded = expandedMaterial === group.material
          const countCopy = group.activeCount > 0
            ? `${group.activeCount}项待核实（涉及${group.affectedBatchCount}个分组）`
            : '0项待核实（已全部确认）'
          return (
            <section className={`w02-v-material ${expanded ? 'expanded' : ''}`} key={group.material}>
              <button type="button" className="w02-v-material-head" aria-expanded={expanded} onClick={() => onToggle(group.material)}>
                <span className={`w02-material-swatch ${materialTone(group.material)}`} />
                <span className="w02-v-material-copy"><strong>{group.material}</strong><small>{countCopy}</small></span>
                {expanded ? <ChevronDown className="w02-v-material-chevron" /> : <ChevronRight className="w02-v-material-chevron" />}
              </button>
              {expanded && (
                <div className="w02-v-material-body">
                  {group.rows.length ? group.rows.map((row) => {
                    const actionLabel = row.status === 'unverified' ? '去核实' : row.status === 'unable_to_verify' ? '查看详情' : null
                    return (
                      <div className="w02-v-task-row" key={row.row_key}>
                        <BatchIdentity row={row} compact onOpen={(batchId) => onOpenBatch(batchId)} />
                        <span className="w02-v-field"><Search className="w02-v-field-icon" /><span>{row.field}</span></span>
                        <span className="w02-v-question">{row.question}</span>
                        <span className="w02-v-status-cell"><VerificationStatusPill status={row.status} /></span>
                        <span className="w02-v-discovered"><strong>{row.discovered_at ?? '—'}</strong><small>{row.discovered_source ?? '来源待确认'}</small></span>
                        {actionLabel && row.canonical_batch_id ? (
                          <button type="button" className="w02-v-action" onClick={() => onOpenBatch(row.canonical_batch_id!, row.focus_target ?? 'human_verification')}><span>{actionLabel}</span><ChevronRight className="w02-v-action-icon" /></button>
                        ) : actionLabel ? (
                          <span className="w02-v-action is-static"><span>{actionLabel}</span><ChevronRight className="w02-v-action-icon" /></span>
                        ) : <span className="w02-v-action-empty">—</span>}
                      </div>
                    )
                  }) : <div className="w02-v-zero">当前材料没有符合筛选条件的核实事项</div>}
                </div>
              )}
            </section>
          )
        }) : <div className="w02-empty"><strong>没有符合当前筛选条件的核实事项</strong><button type="button" onClick={onClear}>清除筛选</button></div>}
      </div>
    </>
  )
}
