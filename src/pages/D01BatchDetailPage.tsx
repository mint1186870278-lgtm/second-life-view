import {
  ArrowLeft,
  BookOpen,
  Camera,
  Check,
  ClipboardCheck,
  CircleHelp,
  Cuboid,
  ExternalLink,
  Grid2X2,
  Hash,
  ImagePlus,
  Layers3,
  Leaf,
  Link2,
  LoaderCircle,
  MapPin,
  Sparkles,
  Upload,
  Wrench,
} from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  fetchDemoComponentDetail,
  generateDemoComponentPreview,
  requestDemoComponentDesignAdvice,
  uploadDemoComponentEvidence,
  type DemoComponentDesignAdvice,
  type DemoComponentDetail,
  type DemoComponentPreview,
} from '../api/demo'
import { useCreationFlow } from '../app/CreationFlowContext'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { getWorkspaceDestinationRoute, WORKSPACE_NAVIGATION_ITEMS } from '../app/workspaceNavigation'
import type { D01NavigationContext } from '../navigation'
import { Button, WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

export function D01BatchDetailPage() {
  return <ProjectSessionGate><D01BatchDetailContent /></ProjectSessionGate>
}

function D01BatchDetailContent() {
  const { batchId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { project } = useProjectSession()
  const { projectDraft } = useCreationFlow()
  const [detail, setDetail] = useState<DemoComponentDetail | null>(null)
  const [loading, setLoading] = useState(Boolean(batchId))
  const [error, setError] = useState<string>()
  const [selectedFile, setSelectedFile] = useState<File>()
  const [imageUrl, setImageUrl] = useState('')
  const [note, setNote] = useState('')
  const [uploading, setUploading] = useState(false)
  const [notice, setNotice] = useState<string>()
  const [designAdvice, setDesignAdvice] = useState<DemoComponentDesignAdvice | null>(null)
  const [designPreview, setDesignPreview] = useState<DemoComponentPreview | null>(null)
  const [designError, setDesignError] = useState<string>()
  const [adviceLoading, setAdviceLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const region = projectDraft.region || project?.region || undefined
  const legacyContext = location.state as D01NavigationContext | null
  const isDemoComponent = Boolean(batchId?.includes('__batch_'))

  useEffect(() => {
    if (!isDemoComponent) {
      setLoading(false)
      setError(undefined)
      return
    }
    if (!batchId) {
      setLoading(false)
      setError('缺少需要核实的构件标识。')
      return
    }
    let active = true
    setLoading(true)
    setDetail(null)
    setError(undefined)
    setDesignAdvice(null)
    setDesignPreview(null)
    setDesignError(undefined)
    fetchDemoComponentDetail(batchId, region)
      .then((nextDetail) => {
        if (active) setDetail(nextDetail)
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError instanceof Error ? requestError.message : '无法读取构件核实详情')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [batchId, isDemoComponent, region])

  async function submitSupplement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!batchId) return
    if (!selectedFile && !imageUrl.trim() && !note.trim()) {
      setNotice('请上传一张照片、填写图片地址或补充现场说明。')
      return
    }
    setUploading(true)
    setNotice(undefined)
    try {
      const result = await uploadDemoComponentEvidence(batchId, {
        file: selectedFile,
        imageUrl,
        note,
      })
      setDetail((current) => current ? { ...current, evidence: [...current.evidence, result.evidence] } : current)
      setSelectedFile(undefined)
      setImageUrl('')
      setNote('')
      if (fileInput.current) fileInput.current.value = ''
      setNotice(`已添加补充材料，当前共 ${result.count} 条用户补证。`)
    } catch (uploadError) {
      setNotice(uploadError instanceof Error ? uploadError.message : '补充材料上传失败')
    } finally {
      setUploading(false)
    }
  }

  async function createDesignAdvice() {
    if (!batchId) return
    setAdviceLoading(true)
    setDesignError(undefined)
    try {
      setDesignAdvice(await requestDemoComponentDesignAdvice(batchId, region))
    } catch (requestError) {
      setDesignError(requestError instanceof Error ? requestError.message : '无法生成改造建议')
    } finally {
      setAdviceLoading(false)
    }
  }

  async function createDesignPreview() {
    if (!batchId || !designAdvice) return
    setPreviewLoading(true)
    setDesignError(undefined)
    try {
      setDesignPreview(await generateDemoComponentPreview(batchId, designAdvice, region))
    } catch (requestError) {
      setDesignError(requestError instanceof Error ? requestError.message : '无法生成改造预览图')
    } finally {
      setPreviewLoading(false)
    }
  }

  const projectName = projectDraft.name || project?.name || '当前项目'
  if (!isDemoComponent && batchId) {
    return <LegacyFixtureDetail projectName={projectName} region={region} navigate={navigate} batchId={batchId} context={legacyContext} />
  }
  if (loading) {
    return <DetailShell projectName={projectName} region={region} navigate={navigate}><div className="d01-state"><LoaderCircle className="spin" />正在加载真实 YOLO 构件与核实信息…</div></DetailShell>
  }
  if (error || !detail) {
    return (
      <DetailShell projectName={projectName} region={region} navigate={navigate}>
        <section className="d01-state is-error">
          <strong>无法打开构件核实详情</strong>
          <p>{error || '当前构件详情不存在。'}</p>
          <Button onClick={() => navigate(ImplementationRoutes.w02)}>返回项目审查</Button>
        </section>
      </DetailShell>
    )
  }

  const { component, scene } = detail
  const requiresVerification = component.evidence_status !== 'supported'
  return (
    <DetailShell projectName={projectName} region={region} navigate={navigate}>
      <button className="d01-back" type="button" onClick={() => navigate(ImplementationRoutes.w02)}><ArrowLeft size={16} />返回项目审查</button>
      <section className="d01-object-header">
        <div className="d01-title-row">
          <h1>{component.name}</h1>
          <span className="d01-quantity-pill">× {component.detected_count} 件</span>
          <span className="d01-recommendation-pill">{component.pathway_label}</span>
        </div>
        <div className="d01-breadcrumb">
          {projectName}<span>/</span>{scene.name}<span>/</span>{component.material}<span>/</span>{component.category_name}<span>/</span>{component.name}
        </div>
      </section>

      <D01SummaryStrip component={component} scene={scene} region={detail.region} />

      <section className="d01-gallery" aria-label="现场证据图组">
        <EvidenceTile source={component.crop_url} label="YOLO 子图" className="hero" />
        {detail.evidence.slice(0, 4).map((item, index) => item.image_url ? (
          <EvidenceTile key={item.id} source={item.image_url} label={item.filename || '用户补充'} className={`d${index + 1}`} />
        ) : <div className={`d01-evidence-note d${index + 1}`} key={item.id}><ClipboardCheck size={18} /><span>{item.note || '已添加文字补充'}</span></div>)}
        <button className="d01-add-photo-tile" type="button" onClick={() => fileInput.current?.click()}>
          <span className="d01-add-photo-icon"><ImagePlus /></span><strong>+ 添加照片</strong><span>共 {detail.evidence.length + 1} 张</span>
        </button>
      </section>

      <section className="d01-core-grid" aria-label="构件核实信息">
        <section className="d01-card d01-assessment-card">
          <div className="d01-card-header"><div className="d01-card-title"><Leaf /><span>当前评估</span></div><span className="d01-badge info">AI 初步评估</span></div>
          <div className="d01-assessment-hero"><span className="d01-path-icon"><Leaf /></span><div><div className="d01-pathway">{detail.assessment.pathway_label}</div><p>{detail.assessment.description}</p></div></div>
          <div className="d01-meta-grid"><div className={`d01-mini-meta ${component.evidence_status}`}><span>证据状态</span><strong><i className={`d01-meta-dot ${component.evidence_status}`} />{detail.assessment.evidence_label}</strong></div><div className="d01-mini-meta"><span>检测置信度</span><strong>{Math.round(component.confidence * 100)}%</strong></div><div className="d01-mini-meta"><span>相似实例</span><strong>{component.detected_count} 件</strong></div></div>
        </section>
        <section className="d01-card">
          <div className="d01-card-header"><div className="d01-card-title"><CircleHelp /><span>{requiresVerification ? `待核实重点（${detail.verification_questions.length}项）` : '施工前复核重点'}</span></div></div>
          <ul className="d01-check-list">
            {detail.verification_questions.map((question) => <li key={question.title}><strong>{question.title}</strong><span>{question.description}</span></li>)}
          </ul>
        </section>
        <section className="d01-card">
          <div className="d01-card-header"><div className="d01-card-title"><Cuboid /><span>可观察事实</span><small>AI 识别</small></div></div>
          <ul className="d01-fact-list">{detail.observable_facts.map((fact) => <li key={fact}><Check size={14} />{fact}</li>)}</ul>
        </section>
      </section>

      <section className="d01-bottom-grid">
        <InfoCard icon={<Camera />} title="360° 现场证据" eyebrow="定位构件上下文">
          <p>打开空间再生编辑器，回看 {component.name} 在 {scene.name} 中的相对位置、周边构件和更多角度。</p>
          <a className="d01-dark-link" href={detail.three_d_url} target="_blank" rel="noreferrer">打开 360° 现场 <ExternalLink size={15} /></a>
        </InfoCard>
        <InfoCard icon={<BookOpen />} title="参考路径" eyebrow="构件专业知识">
          <LinkList links={detail.reference_pathways} empty="暂无可用参考路径。" />
        </InfoCard>
        <InfoCard icon={<MapPin />} title="本地机会" eyebrow={detail.region}>
          <LinkList links={detail.local_opportunities} empty="暂无匹配的本地机会。" local />
        </InfoCard>
      </section>

      <section className="d01-card d01-human-card" id="d01-human-verification">
        <div className="d01-human-header"><div><div className="d01-card-title"><Wrench /><span>{requiresVerification ? '人工核实与补证' : '补充现场证据'}</span></div><p>{requiresVerification ? '逐项补充近景、连接节点与现场观察，避免把尚未确认的状态写成结论。' : '当前评估已有依据；如现场情况发生变化，可继续上传材料保留审查记录。'}</p></div><span className={`d01-badge ${requiresVerification ? 'warn' : 'info'}`}>{component.evidence_label}</span></div>
        <div className="d01-current-instance-bar"><div><span>当前核实对象</span><strong>{component.name} · {scene.name}</strong></div><span>{component.detected_count} 个相似实例</span></div>
        <form className="d01-evidence-form d01-evidence-form--inline" onSubmit={(event) => void submitSupplement(event)}>
          <label><span>补充现场照片</span><input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setSelectedFile(event.currentTarget.files?.[0])} /><small>{selectedFile ? selectedFile.name : '支持 JPG、PNG、WEBP，最大 12MB'}</small></label>
          <label><span>图片地址（可选）</span><input type="url" value={imageUrl} placeholder="https://…" onChange={(event) => setImageUrl(event.target.value)} /></label>
          <label className="d01-evidence-note-field"><span>现场说明（选填）</span><textarea value={note} rows={3} placeholder="例如：左侧脚件有松动，背板未见霉斑。" onChange={(event) => setNote(event.target.value)} /></label>
          <div className="d01-evidence-submit"><Button disabled={uploading}>{uploading ? <><LoaderCircle className="spin" size={16} />上传中…</> : <><Upload size={16} />保存补证</>}</Button>{notice && <p className="d01-form-notice" role="status">{notice}</p>}</div>
        </form>
      </section>

      {component.can_generate_preview && <D01DesignPanel advice={designAdvice} preview={designPreview} error={designError} adviceLoading={adviceLoading} previewLoading={previewLoading} onCreateAdvice={() => void createDesignAdvice()} onCreatePreview={() => void createDesignPreview()} />}
    </DetailShell>
  )
}

function DetailShell({ projectName, region, navigate, children }: {
  projectName: string
  region?: string
  navigate: ReturnType<typeof useNavigate>
  children: ReactNode
}) {
  return (
    <WorkspaceShell
      projectName={projectName}
      projectContextLabel={region}
      items={WORKSPACE_NAVIGATION_ITEMS}
      activeDestination="review"
      onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
      headerCenter={<div className="d01-header-title">构件核实</div>}
      headerAction={<Button className="workspace-context-action d01-return-action" onClick={() => navigate(ImplementationRoutes.w02)}><span>返回项目审查</span></Button>}
      frameClassName="d01-frame"
      contentClassName="d01-main"
    >
      {children}
    </WorkspaceShell>
  )
}

function D01SummaryStrip({ component, scene, region }: {
  component: DemoComponentDetail['component']
  scene: DemoComponentDetail['scene']
  region: string
}) {
  return <section className="d01-summary-strip" aria-label="评估分组摘要">
    <SummaryCell icon={<Layers3 />} label="材料组" value={component.material} sub="Material" />
    <SummaryCell icon={<Cuboid />} label="构件类型" value={component.category_name} sub="Component Type" />
    <SummaryCell icon={<Grid2X2 />} label="构件分组" value={component.name} />
    <SummaryCell icon={<Hash />} label="实例数量" value={`${component.detected_count} 件`} sub="相似构件" />
    <SummaryCell icon={<MapPin />} label="所属场景" value={scene.name} sub={region} />
    <SummaryCell accent icon={<Leaf />} label="建议路径" value={component.pathway_label} sub="基于当前评估" />
    <SummaryCell icon={<span className={`d01-evidence-dot ${component.evidence_status}`} />} label="证据状态" value={component.evidence_label} sub="AI 与现场材料" />
    <SummaryCell icon={<Check />} label="检测置信度" value={`${Math.round(component.confidence * 100)}%`} sub="YOLO 实例识别" />
  </section>
}

function SummaryCell({ icon, label, value, sub, accent = false }: { icon: ReactNode; label: string; value: string; sub?: string; accent?: boolean }) {
  return <div className={`d01-summary-cell ${accent ? 'accent' : ''}`.trim()}>{icon}<div><span>{label}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div></div>
}

function EvidenceTile({ source, label, className }: { source: string; label: string; className: string }) {
  return <figure className={`d01-evidence-photo ${className}`}><img src={source} alt={label} /><figcaption className="d01-image-label">{label}</figcaption></figure>
}

function InfoCard({ icon, title, eyebrow, children }: { icon: ReactNode; title: string; eyebrow: string; children: ReactNode }) {
  return <section className="d01-card d01-bottom-card d01-info-card"><header><span>{icon}</span><div><small>{eyebrow}</small><h2>{title}</h2></div></header>{children}</section>
}

function D01DesignPanel({ advice, preview, error, adviceLoading, previewLoading, onCreateAdvice, onCreatePreview }: {
  advice: DemoComponentDesignAdvice | null
  preview: DemoComponentPreview | null
  error?: string
  adviceLoading: boolean
  previewLoading: boolean
  onCreateAdvice: () => void
  onCreatePreview: () => void
}) {
  return <section className="d01-card d01-design-card" aria-labelledby="d01-design-title">
    <div className="d01-human-header"><div><div className="d01-card-title"><Sparkles /><span id="d01-design-title">Design Agent 改造预览</span></div><p>先生成文字版的材质、颜色、表面与施工建议；确认后才会调用 qwen-image-3.0-pro 生成该构件子图的翻新预览。</p></div><span className="d01-badge info">有依据 · 可生成</span></div>
    {adviceLoading && <div className="d01-design-state"><LoaderCircle className="spin" />Design Agent 正在生成建议…</div>}
    {!adviceLoading && error && <div className="d01-design-state is-error">{error}</div>}
    {!adviceLoading && advice && <div className="d01-design-advice"><DesignAdviceRow label="材质" value={advice.material} /><DesignAdviceRow label="颜色" value={advice.color} /><DesignAdviceRow label="表面" value={advice.surface} /><DesignAdviceRow label="施工" value={advice.construction} /><p>{advice.rationale}</p></div>}
    {preview && <figure className="d01-generated-preview"><img src={preview.image_url} alt="改造后的构件预览" /><figcaption>{preview.is_offline_fallback ? '生成服务未返回图片，当前显示本地回退预览。' : '已由 qwen-image-3.0-pro 生成。'}</figcaption></figure>}
    <div className="d01-design-actions"><Button variant="secondary" disabled={adviceLoading || Boolean(advice)} onClick={onCreateAdvice}>{adviceLoading ? '生成建议中…' : advice ? '已生成文字建议' : '生成文字版改造建议'}</Button>{advice && !preview && <Button disabled={previewLoading} onClick={onCreatePreview}>{previewLoading ? <><LoaderCircle className="spin" size={16} />生成中…</> : <><Leaf size={16} />同意并生成预览图</>}</Button>}</div>
  </section>
}

function DesignAdviceRow({ label, value }: { label: string; value: string }) {
  return <div><strong>{label}</strong><span>{value}</span></div>
}

function LegacyFixtureDetail({
  projectName,
  region,
  navigate,
  batchId,
  context,
}: {
  projectName: string
  region?: string
  navigate: ReturnType<typeof useNavigate>
  batchId: string
  context: D01NavigationContext | null
}) {
  const focusTarget = context?.focus_target ?? 'human_verification'
  return (
    <DetailShell projectName={projectName} region={region} navigate={navigate}>
      <section className="d01-legacy-context">
        <p className="d01-eyebrow">兼容现有项目 Fixture</p>
        <h1>构件核实上下文已保留</h1>
        <p>当前路由来自旧版工作区 fixture；实际 YOLO 构件会在项目审查页中打开真实裁切图与动态核实卡。</p>
        <dl>
          <div><dt>batch_id</dt><dd>{batchId}</dd></div>
          <div><dt>focus_target</dt><dd>{focusTarget}</dd></div>
        </dl>
        <Button onClick={() => navigate(ImplementationRoutes.w02)}>进入项目审查</Button>
      </section>
    </DetailShell>
  )
}

function LinkList({ links, empty, local = false }: {
  links: readonly { title: string; description: string; source_url: string; provenance: string }[]
  empty: string
  local?: boolean
}) {
  if (!links.length) return <p className="d01-empty-copy">{empty}</p>
  return <div className="d01-link-list">
    {links.map((link) => (
      <article key={`${link.title}-${link.source_url}`}>
        <Link2 size={15} />
        <div><strong>{link.title}</strong><p>{link.description}</p></div>
        <span className={`d01-provenance ${link.provenance}`}>{local ? (link.provenance === 'to_confirm' ? '待对接' : '可参考') : (link.provenance === 'verified' ? '已核验' : '待确认')}</span>
      </article>
    ))}
  </div>
}
