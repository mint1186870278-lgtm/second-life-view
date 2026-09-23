import {
  ArrowLeft,
  BookOpen,
  Camera,
  Check,
  ClipboardCheck,
  ExternalLink,
  ImagePlus,
  Leaf,
  Link2,
  LoaderCircle,
  MapPin,
  Upload,
} from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  fetchDemoComponentDetail,
  uploadDemoComponentEvidence,
  type DemoComponentDetail,
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
  return (
    <DetailShell projectName={projectName} region={region} navigate={navigate}>
      <button className="d01-back" type="button" onClick={() => navigate(ImplementationRoutes.w02)}><ArrowLeft size={16} />返回项目审查</button>
      <header className="d01-title-block">
        <div>
          <p className="d01-eyebrow">待核实构件 · YOLO 实例裁切</p>
          <h1>{component.name}</h1>
          <p>{projectName} / {scene.name} / {component.material} / {component.category_name}</p>
        </div>
        <div className="d01-title-badges">
          <span className={`d01-evidence-badge ${component.evidence_status}`}>{component.evidence_label}</span>
          <span className="d01-pathway-badge">{component.pathway_label}</span>
        </div>
      </header>

      <section className="d01-object-layout">
        <figure className="d01-object-photo">
          <img src={component.crop_url} alt={`${component.name} 的真实 YOLO 检测裁切图`} />
          <figcaption><ImagePlus size={15} />真实 YOLO bbox 裁切图 · {component.detected_count} 个相似实例</figcaption>
        </figure>
        <div className="d01-object-summary">
          <SummaryFact label="识别类别" value={component.category_name} />
          <SummaryFact label="初判材质" value={component.material} />
          <SummaryFact label="检测置信度" value={`${Math.round(component.confidence * 100)}%`} />
          <SummaryFact label="项目所在地" value={detail.region} />
          <p>{detail.assessment.description}</p>
        </div>
      </section>

      <section className="d01-evidence-section" aria-labelledby="d01-evidence-title">
        <div className="d01-section-heading">
          <div><h2 id="d01-evidence-title"><Camera size={19} />现场补充材料</h2><p>原始构件子图与用户补充内容会一并用于后续人工核实。</p></div>
          <span>{detail.evidence.length + 1} 项材料</span>
        </div>
        <div className="d01-evidence-layout">
          <div className="d01-evidence-gallery">
            <EvidenceImage source={component.crop_url} label="YOLO 子图" />
            {detail.evidence.map((item) => item.image_url ? <EvidenceImage key={item.id} source={item.image_url} label={item.filename || '用户补充'} /> : (
              <div className="d01-evidence-note" key={item.id}><ClipboardCheck size={18} /><span>{item.note || '已添加文字补充'}</span></div>
            ))}
          </div>
          <form className="d01-evidence-form" onSubmit={(event) => void submitSupplement(event)}>
            <label>
              <span>补充现场照片</span>
              <input
                ref={fileInput}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => setSelectedFile(event.currentTarget.files?.[0])}
              />
              <small>{selectedFile ? selectedFile.name : '支持 JPG、PNG、WEBP，最大 12MB'}</small>
            </label>
            <label>
              <span>图片地址（可选）</span>
              <input type="url" value={imageUrl} placeholder="https://…" onChange={(event) => setImageUrl(event.target.value)} />
            </label>
            <label>
              <span>现场说明（可选）</span>
              <textarea value={note} rows={3} placeholder="例如：左侧脚件有松动，背板未见霉斑。" onChange={(event) => setNote(event.target.value)} />
            </label>
            <Button disabled={uploading}>{uploading ? <><LoaderCircle className="spin" size={16} />上传中…</> : <><Upload size={16} />添加补充</>}</Button>
            {notice && <p className="d01-form-notice" role="status">{notice}</p>}
          </form>
        </div>
      </section>

      <section className="d01-info-grid" aria-label="构件核实信息">
        <InfoCard icon={<Leaf />} title={detail.assessment.title} eyebrow="当前评估">
          <p>{detail.assessment.description}</p>
          <div className="d01-info-inline"><span>证据：{detail.assessment.evidence_label}</span><span>路径：{detail.assessment.pathway_label}</span></div>
        </InfoCard>
        <InfoCard icon={<ClipboardCheck />} title="待核实重点" eyebrow={`${detail.verification_questions.length} 项`}> 
          <ul className="d01-check-list">
            {detail.verification_questions.map((question) => <li key={question.title}><strong>{question.title}</strong><span>{question.description}</span></li>)}
          </ul>
        </InfoCard>
        <InfoCard icon={<Check />} title="可观察事实" eyebrow="AI 识别">
          <ul className="d01-fact-list">{detail.observable_facts.map((fact) => <li key={fact}><Check size={14} />{fact}</li>)}</ul>
        </InfoCard>
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
      headerAction={<Button className="d01-return-action" onClick={() => navigate(ImplementationRoutes.w02)}>返回项目审查</Button>}
      contentClassName="d01-main"
    >
      {children}
    </WorkspaceShell>
  )
}

function SummaryFact({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value}</strong></div>
}

function EvidenceImage({ source, label }: { source: string; label: string }) {
  return <figure className="d01-evidence-image"><img src={source} alt={label} /><figcaption>{label}</figcaption></figure>
}

function InfoCard({ icon, title, eyebrow, children }: { icon: ReactNode; title: string; eyebrow: string; children: ReactNode }) {
  return <section className="d01-info-card"><header><span>{icon}</span><div><small>{eyebrow}</small><h2>{title}</h2></div></header>{children}</section>
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
