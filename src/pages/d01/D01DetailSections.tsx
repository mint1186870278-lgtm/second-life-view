import {
  ArrowLeft, BookOpen, Camera, Check, ChevronRight, CircleHelp, Clock3, Cuboid,
  Grid2X2, Hash, ImagePlus, Layers3, Leaf, MapPin, Wrench,
} from 'lucide-react'
import { useRef, type ReactNode } from 'react'
import type { HumanVerificationDraft } from '../../application'
import { d01DemoProjection } from '../../config'
import type { ComponentInstanceId, HumanVerificationFieldKey } from '../../domain'
import { HUMAN_VERIFICATION_FIELD_LABELS } from '../../domain'
import {
  D01_EVIDENCE_LABELS, D01_PATHWAY_LABELS,
  type D01BatchDetailReadModel,
} from '../../selectors'

const MATERIAL_ENGLISH: Record<string, string> = {
  木材: 'Timber', 金属: 'Metal', 玻璃: 'Glass', 混凝土: 'Concrete', 植栽: 'Planting', 其他: 'Other',
}

export const D01_FIELD_PROMPTS: Record<HumanVerificationFieldKey, string> = {
  fixing_method: '确认是否可无损拆卸',
  hidden_damage: '检查内部是否存在腐朽或结构损伤',
  surface_treatment: '确认是否有涂层 / 防腐处理',
}

export const D01_FIELD_OPTIONS: Record<HumanVerificationFieldKey, readonly string[]> = {
  fixing_method: ['可拆卸螺丝/螺栓', '钉固', '胶粘', '不可判断'],
  hidden_damage: ['未发现', '发现局部损伤', '无法现场确认'],
  surface_treatment: ['已确认有', '已确认无', '无法确认'],
}

export function isCompleteVerificationDraft(draft: HumanVerificationDraft): boolean {
  return Object.values(draft.values).every(Boolean)
}

export function D01BackButton({ label, onClick }: { label: string; onClick: () => void }) {
  return <button className="d01-back" type="button" onClick={onClick}><ArrowLeft /> <span>{label}</span></button>
}

export function D01ObjectHeader({ detail, projectName }: { detail: D01BatchDetailReadModel; projectName: string }) {
  const { batch, scene } = detail
  return <section className="d01-object-header">
    <div className="d01-title-row">
      <h1>{batch.batch_label}</h1>
      <span className="d01-quantity-pill">× {detail.quantity}件</span>
      <span className="d01-recommendation-pill">{D01_PATHWAY_LABELS[batch.pathway]}</span>
    </div>
    <div className="d01-breadcrumb">
      {projectName}<span>/</span>场景 {String(detail.scene_index).padStart(2, '0')} · {scene.name}
      <span>/</span>{batch.material_group}<span>/</span>{batch.component_type}<span>/</span>{batch.batch_label}
    </div>
  </section>
}

export function D01SummaryStrip({ detail, verifiedCount }: { detail: D01BatchDetailReadModel; verifiedCount: number }) {
  const { batch, scene } = detail
  return <section className="d01-summary-strip" aria-label="评估分组摘要">
    <SummaryCell icon={<Layers3 />} label="材料组" value={batch.material_group} sub={MATERIAL_ENGLISH[batch.material_group] ?? 'Material'} />
    <SummaryCell icon={<Cuboid />} label="构件类型" value={batch.component_type} sub="Component Type" />
    <SummaryCell icon={<Grid2X2 />} label="分组" value={batch.batch_label} />
    <SummaryCell icon={<Hash />} label="实例数量" value={`${detail.quantity}件`} sub="相似构件" />
    <SummaryCell icon={<MapPin />} label="所属场景" value={`场景 ${String(detail.scene_index).padStart(2, '0')}`} sub={scene.name} />
    <SummaryCell accent icon={<Leaf />} label="建议路径" value={D01_PATHWAY_LABELS[batch.pathway]} sub="基于当前评估" />
    <SummaryCell icon={<span className={`d01-evidence-dot ${batch.evidence_status}`} />} label="证据状态" value={D01_EVIDENCE_LABELS[batch.evidence_status]} sub={`已核实 ${verifiedCount} / ${detail.quantity}件`} />
    <SummaryCell icon={<Clock3 />} label="上次更新" value={d01DemoProjection.updated_date} sub="AI识别 + 人工核实" />
  </section>
}

function SummaryCell({ icon, label, value, sub, accent = false }: {
  icon: ReactNode; label: string; value: string; sub?: string; accent?: boolean
}) {
  return <div className={`d01-summary-cell ${accent ? 'accent' : ''}`.trim()}>
    {icon}<div><span>{label}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div>
  </div>
}

export function D01EvidenceGallery({ evidenceCount, onAddFiles }: {
  evidenceCount: number
  onAddFiles: (files: readonly File[]) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  return <section className="d01-gallery" aria-label="现场证据图组">
    {d01DemoProjection.evidence_labels.map((label, index) => (
      <div className={`d01-evidence-photo ${index === 0 ? 'hero' : `detail d${index}`}`} key={label}>
        <span className="d01-image-label">{label}</span>
      </div>
    ))}
    <button className="d01-add-photo-tile" type="button" onClick={() => inputRef.current?.click()}>
      <span className="d01-add-photo-icon"><ImagePlus /></span>
      <strong>+ 添加照片</strong>
      <span>共 {evidenceCount} 张</span>
    </button>
    <input ref={inputRef} aria-label="选择现场补充照片" type="file" accept="image/*" multiple hidden onChange={(event) => {
      const files = [...(event.currentTarget.files ?? [])]
      if (files.length) onAddFiles(files)
      event.currentTarget.value = ''
    }} />
  </section>
}

export function D01AssessmentCard({ detail, verifiedCount, onOpenPathways }: {
  detail: D01BatchDetailReadModel
  verifiedCount: number
  onOpenPathways: () => void
}) {
  const { batch } = detail
  return <section className="d01-card d01-assessment-card">
    <div className="d01-card-header">
      <div className="d01-card-title"><Leaf /><span>当前评估</span></div>
      <span className="d01-badge info">AI 初步评估</span>
    </div>
    <div className="d01-assessment-hero">
      <div className="d01-path-icon"><Leaf /></div>
      <div>
        <div className="d01-pathway">{D01_PATHWAY_LABELS[batch.pathway]}</div>
        <p>{d01DemoProjection.assessment_rationale}</p>
      </div>
    </div>
    <div className="d01-meta-grid">
      <div className={`d01-mini-meta ${batch.evidence_status}`}>
        <span>证据状态</span>
        <strong><i className={`d01-meta-dot ${batch.evidence_status}`} />{D01_EVIDENCE_LABELS[batch.evidence_status]}</strong>
      </div>
      <div className="d01-mini-meta"><span>核实进度</span><strong>{verifiedCount} / {detail.quantity}件</strong></div>
      <div className="d01-mini-meta"><span>评估日期</span><strong>{d01DemoProjection.assessment_date}</strong></div>
    </div>
    <button className="d01-light-action" type="button" onClick={onOpenPathways}>查看全部6条路径 <ChevronRight /></button>
  </section>
}

export function D01VerificationSummary({ detail, savedDrafts, onFocus }: {
  detail: D01BatchDetailReadModel
  savedDrafts: ReadonlyMap<ComponentInstanceId, HumanVerificationDraft>
  onFocus: (key: HumanVerificationFieldKey) => void
}) {
  return <section className="d01-card">
    <div className="d01-card-header"><div className="d01-card-title"><CircleHelp /><span>待核实类型（3类）</span></div></div>
    <div className="d01-verification-summary-list">
      {detail.verification_fields.map(({ key, item }, index) => {
        const done = detail.instances.filter((instance) => Boolean(savedDrafts.get(instance.component_instance_id)?.values[key])).length
        const complete = detail.instances.length > 0 && done === detail.instances.length
        return <button className="d01-verification-summary-row" type="button" key={key} onClick={() => onFocus(key)}>
          <span className={`d01-number-badge ${complete ? 'done' : ''}`}>{complete ? <Check /> : index + 1}</span>
          <span><strong>{HUMAN_VERIFICATION_FIELD_LABELS[key]}</strong><small>{item?.question ?? D01_FIELD_PROMPTS[key]} · {done} / {detail.quantity} 已核实</small></span>
          <span className={`d01-row-status ${complete ? 'done' : ''}`}>{complete ? '已完成' : '待核实'}</span>
        </button>
      })}
    </div>
    <button className="d01-light-action right" type="button" onClick={() => onFocus('fixing_method')}>进入人工核实 <ChevronRight /></button>
  </section>
}

export function D01ObservableFacts() {
  return <section className="d01-card">
    <div className="d01-card-header"><div className="d01-card-title"><Cuboid /><span>可观察事实</span><small>AI识别</small></div></div>
    <div className="d01-facts-list">
      {d01DemoProjection.observable_facts.map((fact) => <div className="d01-fact-row" key={fact}><span className="d01-check-disc"><Check /></span><span>{fact}</span></div>)}
    </div>
  </section>
}

export function D01SupportingCards({ onDeferred }: { onDeferred: (message: string) => void }) {
  return <section className="d01-bottom-grid">
    <section className="d01-card d01-bottom-card">
      <div className="d01-card-header"><div className="d01-card-title"><Camera /><span>360° 现场证据</span></div></div>
      <div className="d01-360-body">
        <div className="d01-360-thumb"><span>360°</span></div>
        <div className="d01-360-copy">
          <p>查看该构件在 360° 现场的真实位置、周边环境及更多角度，辅助判断构件状况与拆卸条件。</p>
          <button className="d01-dark-btn" type="button" onClick={() => onDeferred('360 Evidence Viewer：下一层沉浸查看层待接入')}>打开 360° 现场</button>
        </div>
      </div>
    </section>
    <section className="d01-card d01-bottom-card">
      <div className="d01-card-header">
        <div className="d01-card-title"><BookOpen /><span>参考路径</span><small>全球案例 · 行业方法 · 指南</small></div>
        <button className="d01-header-action" type="button" onClick={() => onDeferred('参考来源：下一步接入 Source Drawer / Expand')}>查看全部 <ChevronRight /></button>
      </div>
      <div className="d01-reference-grid">
        {d01DemoProjection.references.map((reference, index) => <button className="d01-reference-item" type="button" key={reference.title} onClick={() => onDeferred('参考来源详情：下一步接入 Source Drawer')}>
          <span className={`d01-ref-thumb r${index + 1}`} />
          <span className="d01-ref-copy"><strong>{reference.title}</strong><small>{reference.copy}</small><span>{reference.tags.map((tag) => <em key={tag}>{tag}</em>)}</span></span>
          <ChevronRight />
        </button>)}
      </div>
      <button className="d01-guideline-row" type="button" onClick={() => onDeferred('参考来源详情：下一步接入 Source Drawer')}>
        <span className="d01-ref-thumb r3" />
        <span><strong>{d01DemoProjection.guideline.title}</strong><small>{d01DemoProjection.guideline.copy}</small></span>
        <ChevronRight />
      </button>
    </section>
    <section className="d01-card d01-bottom-card" id="d01-local-opportunity">
      <div className="d01-card-header">
        <div className="d01-card-title"><MapPin /><span>本地机会</span><small>南京 · 江苏</small></div>
        <button className="d01-header-action" type="button" onClick={() => onDeferred('Local Opportunity Detail：下一层页面待接入')}>查看全部 <ChevronRight /></button>
      </div>
      <div className="d01-local-list">
        {d01DemoProjection.local_opportunities.map((opportunity, index) => <button className="d01-local-row" type="button" key={opportunity.title} onClick={() => onDeferred('Local Opportunity Detail：下一层页面待接入')}>
          <span className={`d01-local-thumb l${index + 1}`} />
          <span><strong>{opportunity.title}</strong><small>{opportunity.copy}</small></span>
          <span className={`d01-state-pill ${opportunity.tone}`}>{opportunity.status}</span>
        </button>)}
      </div>
    </section>
  </section>
}

type InstanceStatus = '未核实' | '进行中' | '已核实'

export function D01HumanVerification({ detail, selectedInstanceId, draft, saved, verifiedCount, hasVariance, focusKey, saving, notice, onSelectInstance, onChangeValue, onChangeNote, onSave, getInstanceStatus }: {
  detail: D01BatchDetailReadModel
  selectedInstanceId: ComponentInstanceId
  draft: HumanVerificationDraft
  saved: HumanVerificationDraft
  verifiedCount: number
  hasVariance: boolean
  focusKey: HumanVerificationFieldKey | null
  saving: boolean
  notice: string
  onSelectInstance: (id: ComponentInstanceId) => void
  onChangeValue: (key: HumanVerificationFieldKey, value: string) => void
  onChangeNote: (note: string) => void
  onSave: () => void
  getInstanceStatus: (id: ComponentInstanceId) => InstanceStatus
}) {
  const selectedIndex = Math.max(0, detail.instances.findIndex((instance) => instance.component_instance_id === selectedInstanceId))
  const dirty = JSON.stringify(draft) !== JSON.stringify(saved)
  return <section className="d01-card d01-human-card" id="d01-human-verification">
    <div className="d01-human-header">
      <div><div className="d01-card-title"><Wrench /><span>人工核实</span></div><p>逐件确认当前分组中无法仅靠图像稳定判断的关键事实。每次保存只作用于当前实例。</p></div>
      <span className="d01-badge warn">已核实 {verifiedCount} / {detail.quantity}件</span>
    </div>
    <div className="d01-instance-toolbar">
      <div className="d01-instance-toolbar-label">组内实例</div>
      <div className="d01-instance-strip">
        {detail.instances.map((instance, index) => {
          const status = getInstanceStatus(instance.component_instance_id)
          const active = instance.component_instance_id === selectedInstanceId
          return <button className={`d01-instance-chip ${status === '已核实' ? 'verified' : status === '进行中' ? 'progress' : 'unverified'} ${active ? 'active' : ''}`} type="button" key={instance.component_instance_id} aria-pressed={active} onClick={() => onSelectInstance(instance.component_instance_id)}>
            <span className="d01-instance-index">{String(index + 1).padStart(2, '0')}</span><span className="d01-instance-status">{status}</span>
          </button>
        })}
      </div>
    </div>
    {hasVariance && <div className="d01-group-warning" role="status"><strong>组内核实结果存在差异</strong><span>建议复核当前分组。当前版本不会自动拆分分组。</span></div>}
    <div className="d01-current-instance-bar"><div><span>当前核实对象</span><strong>{detail.batch.batch_label} · 实例 {String(selectedIndex + 1).padStart(2, '0')}</strong></div><span>{getInstanceStatus(selectedInstanceId)}</span></div>
    <div className="d01-field-stack">
      {detail.verification_fields.map(({ key, item }) => <div className={`d01-verification-field ${focusKey === key ? 'focus-pulse' : ''}`} id={`d01-field-${key}`} key={key}>
        <div className="d01-field-head"><div><strong>{HUMAN_VERIFICATION_FIELD_LABELS[key]}</strong><span>{item?.question ?? D01_FIELD_PROMPTS[key]}</span></div><span className={`d01-field-state ${saved.values[key] ? 'done' : ''}`}>{saved.values[key] ? '已核实' : '待核实'}</span></div>
        <div className={`d01-option-grid ${D01_FIELD_OPTIONS[key].length === 4 ? 'four' : ''}`}>{D01_FIELD_OPTIONS[key].map((option) => <button className={`d01-option-card ${draft.values[key] === option ? 'selected' : ''}`} type="button" aria-pressed={draft.values[key] === option} key={option} onClick={() => onChangeValue(key, option)}><span className="d01-radio" /><span>{option}</span></button>)}</div>
      </div>)}
    </div>
    <label className="d01-note-field"><span>补充说明（选填）</span><textarea value={draft.note} placeholder="补充当前实例的现场观察、拆卸条件或其他核实信息" onChange={(event) => onChangeNote(event.target.value)} /></label>
    <div className="d01-save-row"><div className="d01-save-notice" aria-live="polite">{notice}</div><button className="d01-save-btn" type="button" disabled={!dirty || saving} onClick={onSave}>{saving ? '保存中…' : '保存当前实例'}</button></div>
  </section>
}
