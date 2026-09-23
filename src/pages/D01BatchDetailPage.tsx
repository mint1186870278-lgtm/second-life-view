import { ChevronDown, MapPin, Plus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import type { HumanVerificationDraft, HumanVerificationService } from '../application'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { getWorkspaceDestinationRoute, WORKSPACE_NAVIGATION_ITEMS } from '../app/workspaceNavigation'
import { d01DemoProjection } from '../config'
import { d01HumanVerificationService } from '../data'
import type { AssessmentBatchId, ComponentInstanceId, HumanVerificationFieldKey } from '../domain'
import type { D01NavigationContext } from '../navigation'
import { selectD01BatchDetail } from '../selectors'
import { EmptyState, WorkspaceShell, type WorkspaceDestination } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'
import {
  D01AssessmentCard, D01BackButton, D01EvidenceGallery, D01HumanVerification,
  D01ObjectHeader, D01ObservableFacts, D01SummaryStrip, D01SupportingCards,
  D01VerificationSummary, isCompleteVerificationDraft,
} from './d01/D01DetailSections'
import { D01SidebarSupplement } from './d01/D01Sidebar'

interface VerificationRecord {
  saved: HumanVerificationDraft
  draft: HumanVerificationDraft
}

function emptyDraft(): HumanVerificationDraft {
  return {
    values: { fixing_method: null, hidden_damage: null, surface_treatment: null },
    note: '',
  }
}

function cloneDraft(draft: HumanVerificationDraft): HumanVerificationDraft {
  return { values: { ...draft.values }, note: draft.note }
}

function draftsEqual(left: HumanVerificationDraft, right: HumanVerificationDraft): boolean {
  return left.note === right.note
    && left.values.fixing_method === right.values.fixing_method
    && left.values.hidden_damage === right.values.hidden_damage
    && left.values.surface_treatment === right.values.surface_treatment
}

export function D01BatchDetailPage({ verificationService = d01HumanVerificationService }: {
  verificationService?: HumanVerificationService
}) {
  return <ProjectSessionGate><D01BatchDetailContent verificationService={verificationService} /></ProjectSessionGate>
}

function D01BatchDetailContent({ verificationService }: { verificationService: HumanVerificationService }) {
  const { batchId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { project, scenes, componentInstances, assessmentBatches, verificationItems } = useProjectSession()
  const routeBatchId = decodeURIComponent(batchId ?? '') as AssessmentBatchId
  const suppliedContext = location.state as D01NavigationContext | null
  const context = suppliedContext?.batch_id === routeBatchId ? suppliedContext : null
  const source = context?.source ?? 'view'
  const detail = useMemo(() => selectD01BatchDetail(
    project!.project_id, routeBatchId, scenes, componentInstances, assessmentBatches, verificationItems,
  ), [assessmentBatches, componentInstances, project, routeBatchId, scenes, verificationItems])
  const [records, setRecords] = useState<Record<string, VerificationRecord>>({})
  const [selectedInstanceId, setSelectedInstanceId] = useState<ComponentInstanceId | null>(null)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [feedback, setFeedback] = useState('')
  const [focusKey, setFocusKey] = useState<HumanVerificationFieldKey | null>(null)
  const [evidenceCounts, setEvidenceCounts] = useState<Record<string, number>>({})
  const [pendingAction, setPendingAction] = useState<(() => void) | null>(null)
  const [contextOpen, setContextOpen] = useState(false)

  useEffect(() => {
    if (!detail) return
    setRecords((current) => {
      const next = { ...current }
      detail.instances.forEach((instance) => {
        if (!next[instance.component_instance_id]) {
          const draft = emptyDraft()
          next[instance.component_instance_id] = { saved: cloneDraft(draft), draft }
        }
      })
      return next
    })
    setSelectedInstanceId(detail.instances[0]?.component_instance_id ?? null)
    setNotice('')
  }, [detail?.batch.batch_id])

  useEffect(() => {
    if (!detail) return
    const target = context?.focus_target
    if (!target) return
    const timer = window.setTimeout(() => focusTarget(target), 50)
    return () => window.clearTimeout(timer)
  }, [context?.focus_target, detail?.batch.batch_id])

  const selectedRecord = selectedInstanceId ? records[selectedInstanceId] : undefined
  const fallbackDraft = emptyDraft()
  const saved = selectedRecord?.saved ?? fallbackDraft
  const draft = selectedRecord?.draft ?? fallbackDraft
  const dirty = Boolean(selectedRecord && !draftsEqual(selectedRecord.draft, selectedRecord.saved))

  useEffect(() => {
    if (!dirty) return
    const protect = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', protect)
    return () => window.removeEventListener('beforeunload', protect)
  }, [dirty])

  if (!detail || !detail.instances.length || !selectedInstanceId) {
    return <WorkspaceShell projectName={project?.name ?? '当前项目'} projectContextLabel={project?.region} items={WORKSPACE_NAVIGATION_ITEMS} activeDestination={source === 'view' ? 'view' : 'review'} onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))} contentClassName="d01-main"><EmptyState title="未找到评估分组" description="请从再生视图或项目审查重新选择一个评估分组。" /></WorkspaceShell>
  }

  const activeDetail = detail
  const activeInstanceId = selectedInstanceId

  const savedDrafts = new Map(detail.instances.map((instance) => [
    instance.component_instance_id,
    records[instance.component_instance_id]?.saved ?? emptyDraft(),
  ]))
  const verifiedCount = detail.instances.filter((instance) => isCompleteVerificationDraft(savedDrafts.get(instance.component_instance_id)!)).length
  const hasVariance = (['fixing_method', 'hidden_damage', 'surface_treatment'] as HumanVerificationFieldKey[]).some((key) => {
    const values = detail.instances.map((instance) => savedDrafts.get(instance.component_instance_id)?.values[key]).filter(Boolean)
    return new Set(values).size > 1
  })
  const evidenceCount = evidenceCounts[detail.batch.batch_id] ?? d01DemoProjection.evidence_count

  function guard(action: () => void) {
    if (dirty) setPendingAction(() => action)
    else action()
  }

  function discardAndContinue() {
    setRecords((current) => ({ ...current, [selectedInstanceId!]: { ...current[selectedInstanceId!], draft: cloneDraft(current[selectedInstanceId!].saved) } }))
    const action = pendingAction
    setPendingAction(null)
    action?.()
  }

  function focusTarget(target: string) {
    if (target === 'local_opportunity') {
      document.getElementById('d01-local-opportunity')?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
      return
    }
    const key = target === 'human_verification' ? null : target as HumanVerificationFieldKey
    setFocusKey(key)
    document.getElementById(key ? `d01-field-${key}` : 'd01-human-verification')?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
    if (key) window.setTimeout(() => setFocusKey(null), 900)
  }

  function returnToSource() {
    const route = source === 'view' ? ImplementationRoutes.w01 : ImplementationRoutes.w02
    navigate(route, { state: context ? { d01ReturnState: context.return_state } : undefined })
  }

  function selectBatch(nextBatchId: AssessmentBatchId) {
    guard(() => {
      const nextContext = context ? { ...context, batch_id: nextBatchId } as D01NavigationContext : undefined
      navigate(ImplementationRoutes.d01.replace(':batchId', encodeURIComponent(nextBatchId)), { state: nextContext })
    })
  }

  function navigateWorkspace(destination: WorkspaceDestination) {
    guard(() => navigate(getWorkspaceDestinationRoute(destination)))
  }

  function selectInstance(instanceId: ComponentInstanceId) {
    guard(() => {
      setSelectedInstanceId(instanceId)
      setNotice('')
    })
  }

  function updateDraft(update: (current: HumanVerificationDraft) => HumanVerificationDraft) {
    setRecords((current) => {
      const record = current[activeInstanceId] ?? { saved: emptyDraft(), draft: emptyDraft() }
      return { ...current, [activeInstanceId]: { ...record, draft: update(record.draft) } }
    })
    setNotice('')
  }

  async function saveVerification() {
    setSaving(true)
    setNotice(`正在保存实例 ${String(activeDetail.instances.findIndex((item) => item.component_instance_id === activeInstanceId) + 1).padStart(2, '0')}…`)
    try {
      const result = await verificationService.submitDraft({
        batch_id: activeDetail.batch.batch_id,
        component_instance_id: activeInstanceId,
        draft,
      })
      setRecords((current) => ({
        ...current,
        [activeInstanceId]: {
          saved: cloneDraft(result.accepted_draft),
          draft: cloneDraft(result.accepted_draft),
        },
      }))
      setNotice('当前实例核实结果已保存。')
      setFeedback('当前实例核实结果已保存')
    } catch (error: unknown) {
      setNotice(error instanceof Error ? error.message : '保存失败，请重试。')
    } finally {
      setSaving(false)
    }
  }

  function instanceStatus(instanceId: ComponentInstanceId): '未核实' | '进行中' | '已核实' {
    const instanceSaved = records[instanceId]?.saved
    if (!instanceSaved) return '未核实'
    if (isCompleteVerificationDraft(instanceSaved)) return '已核实'
    return Object.values(instanceSaved.values).some(Boolean) || Boolean(instanceSaved.note) ? '进行中' : '未核实'
  }

  const backLabel = source === 'view' ? '返回再生视图' : '返回项目审查'
  return <>
    <WorkspaceShell
      projectName={`${project?.name ?? '当前项目'} · ${detail.scene.name}`}
      projectContextLabel={project?.region}
      items={WORKSPACE_NAVIGATION_ITEMS}
      activeDestination={source === 'view' ? 'view' : 'review'}
      onNavigate={navigateWorkspace}
      frameClassName="d01-frame"
      contentClassName="d01-main"
      projectContext={<div className={`d01-project-context ${contextOpen ? 'open' : ''}`}>
        <button className="d01-context-button" type="button" aria-expanded={contextOpen} onClick={() => setContextOpen((open) => !open)}>
          <span><strong>{project?.name} · {detail.scene.name}</strong><small><MapPin />{project?.region}</small></span><ChevronDown />
        </button>
        {contextOpen && <div className="d01-context-menu">
          <button type="button" onClick={() => setContextOpen(false)}>{project?.name} · 当前项目</button>
          <button type="button" onClick={() => guard(() => navigate(ImplementationRoutes.c01))}><Plus /> 新建再生评估项目</button>
        </div>}
      </div>}
      headerAction={null}
      sidebarSupplement={<D01SidebarSupplement detail={detail} scenes={scenes} onSelectBatch={selectBatch} />}
    >
      <D01BackButton label={backLabel} onClick={() => guard(returnToSource)} />
      <D01ObjectHeader detail={detail} projectName={project?.name ?? '当前项目'} />
      <D01SummaryStrip detail={detail} verifiedCount={verifiedCount} />
      <D01EvidenceGallery evidenceCount={evidenceCount} onAddFiles={(files) => {
        setEvidenceCounts((current) => ({ ...current, [detail.batch.batch_id]: evidenceCount + files.length }))
        setFeedback(`已添加 ${files.length} 张现场补充照片`)
      }} />
      <section className="d01-core-grid">
        <D01AssessmentCard detail={detail} verifiedCount={verifiedCount} onOpenPathways={() => setFeedback('Pathway Detail：下一层页面按已确认 D01 child layer 接入')} />
        <D01VerificationSummary detail={detail} savedDrafts={savedDrafts} onFocus={focusTarget} />
        <D01ObservableFacts />
      </section>
      <D01SupportingCards onDeferred={setFeedback} />
      <D01HumanVerification
        detail={detail}
        selectedInstanceId={selectedInstanceId}
        draft={draft}
        saved={saved}
        verifiedCount={verifiedCount}
        hasVariance={hasVariance}
        focusKey={focusKey}
        saving={saving}
        notice={notice}
        onSelectInstance={selectInstance}
        onChangeValue={(key, value) => updateDraft((current) => ({ ...current, values: { ...current.values, [key]: value } }))}
        onChangeNote={(note) => updateDraft((current) => ({ ...current, note }))}
        onSave={() => void saveVerification()}
        getInstanceStatus={instanceStatus}
      />
    </WorkspaceShell>
    {feedback && <div className="d01-toast" role="status"><span>{feedback}</span><button type="button" aria-label="关闭提示" onClick={() => setFeedback('')}>×</button></div>}
    {pendingAction && <div className="d01-dialog-backdrop"><section className="d01-discard-dialog" role="dialog" aria-modal="true" aria-labelledby="d01-discard-title"><h2 id="d01-discard-title">放弃未保存的修改？</h2><p>当前实例有尚未保存的人工核实内容。</p><div><button type="button" onClick={() => setPendingAction(null)}>继续编辑</button><button className="danger" type="button" onClick={discardAndContinue}>放弃并继续</button></div></section></div>}
  </>
}
