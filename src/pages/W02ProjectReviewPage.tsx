import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { getWorkspaceDestinationRoute, WORKSPACE_NAVIGATION_ITEMS } from '../app/workspaceNavigation'
import { w02DemoProjection } from '../config'
import type { AssessmentBatchId, VerificationItem } from '../domain'
import type { D01NavigationContext, W02DraftSummaryFilter } from '../navigation'
import {
  selectW02ASummary,
  selectW02BSummary,
  selectW02DraftBatches,
  selectW02VerificationRows,
} from '../selectors'
import { Button, WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'
import {
  W02AttentionRail,
  W02DraftSummary,
  W02DraftTable,
  W02DraftToolbar,
  W02ReviewTabs,
  W02VerificationSummary,
  W02VerificationTable,
  W02VerificationToolbar,
  type W02AttentionRow,
  type W02DraftDisplayRow,
  type W02DraftFilters,
  type W02MaterialGroup,
  type W02Tab,
  type W02VerificationDisplayRow,
  type W02VerificationFilters,
} from './w02/W02ReviewComponents'

const DRAFT_PAGE_SIZE = 7
const ACTIVE_VERIFICATION_STATUSES = new Set(['unverified', 'unable_to_verify'])

const DEFAULT_DRAFT_FILTERS: W02DraftFilters = {
  material: 'all',
  scene: 'all',
  evidence: 'all',
  review: 'all',
  search: '',
}

const DEFAULT_VERIFICATION_FILTERS: W02VerificationFilters = {
  material: 'all',
  scene: 'all',
  type: 'all',
  status: 'active',
  search: '',
}

export function W02ProjectReviewPage() {
  return <ProjectSessionGate><W02ProjectReviewContent /></ProjectSessionGate>
}

function W02ProjectReviewContent() {
  const {
    project,
    scenes,
    componentInstances,
    assessmentBatches,
    verificationItems,
  } = useProjectSession()
  const navigate = useNavigate()
  const [tab, setTab] = useState<W02Tab>('draft')
  const [draftFilters, setDraftFilters] = useState<W02DraftFilters>(DEFAULT_DRAFT_FILTERS)
  const [summaryFilter, setSummaryFilter] = useState<W02DraftSummaryFilter>('all')
  const [page, setPage] = useState(1)
  const [verificationFilters, setVerificationFilters] = useState<W02VerificationFilters>(DEFAULT_VERIFICATION_FILTERS)
  const [expandedMaterial, setExpandedMaterial] = useState<string | null>('木材')
  const projectId = project!.project_id

  const canonicalDraftRows = useMemo(() => selectW02DraftBatches(
    projectId,
    scenes,
    componentInstances,
    assessmentBatches,
    verificationItems,
  ), [assessmentBatches, componentInstances, projectId, scenes, verificationItems])

  const canonicalVerificationRows = useMemo(() => selectW02VerificationRows(
    projectId,
    scenes,
    assessmentBatches,
    verificationItems,
  ), [assessmentBatches, projectId, scenes, verificationItems])

  const draftRows = useMemo<W02DraftDisplayRow[]>(() => [
    ...canonicalDraftRows.map((row) => ({
      row_key: `canonical:${row.batch_id}`,
      canonical_batch_id: row.batch_id,
      material_group: row.material_group,
      component_type: row.component_type,
      batch_label: row.batch_label,
      quantity: row.quantity,
      scene_key: row.scene_id,
      scene_name: row.scene_name,
      scene_index: row.scene_index,
      pathway: row.pathway,
      evidence_status: row.evidence_status,
      review_status: row.review_status,
      pending_verification_count: row.pending_verification_count,
      attention: row.attention,
      attention_reason: row.attention_reason,
    })),
    ...w02DemoProjection.batch_rows.map((row) => ({
      row_key: `presentation:${row.presentation_batch_id}`,
      material_group: row.material_group,
      component_type: row.component_type,
      batch_label: row.batch_label,
      quantity: row.quantity,
      scene_key: row.scene_key,
      scene_name: row.scene_name,
      scene_index: row.scene_index,
      pathway: row.pathway,
      evidence_status: row.evidence_status,
      review_status: row.review_status,
      pending_verification_count: row.pending_verification_count,
      attention: row.attention,
      attention_reason: row.attention_reason,
    })),
  ], [canonicalDraftRows])

  const verificationRows = useMemo<W02VerificationDisplayRow[]>(() => [
    ...canonicalVerificationRows.map((row) => ({
      row_key: `canonical:${row.verification_id}`,
      group_key: `canonical:${row.batch_id}`,
      canonical_batch_id: row.batch_id,
      material_group: row.material_group,
      batch_label: row.batch_label,
      scene_key: row.scene_id,
      scene_name: row.scene_name,
      scene_index: row.scene_index,
      field: row.field,
      question: row.question,
      verification_type: row.verification_type,
      status: row.status,
      focus_target: row.focus_target,
      discovered_at: row.discovered_at,
      discovered_source: row.discovered_source,
    })),
    ...w02DemoProjection.verification_rows.map((row) => ({
      row_key: `presentation:${row.presentation_verification_id}`,
      group_key: `presentation:${row.presentation_batch_id}`,
      material_group: row.material_group,
      batch_label: row.batch_label,
      scene_key: row.scene_key,
      scene_name: row.scene_name,
      scene_index: row.scene_index,
      field: row.field,
      question: row.question,
      verification_type: row.verification_type,
      status: row.status,
      discovered_at: row.discovered_at,
      discovered_source: row.discovered_source,
    })),
  ], [canonicalVerificationRows])

  const draftSummary = useMemo(
    () => selectW02ASummary(projectId, scenes, assessmentBatches),
    [assessmentBatches, projectId, scenes],
  )

  const materialOptions = useMemo(
    () => [{ value: 'all', label: '全部材料' }, ...[...new Set(draftRows.map((row) => row.material_group))].map((material) => ({ value: material, label: material }))],
    [draftRows],
  )
  const sceneOptions = useMemo(() => {
    const options = new Map<string, string>()
    draftRows.forEach((row) => options.set(row.scene_key, row.scene_name))
    return [{ value: 'all', label: '全部场景' }, ...[...options].map(([value, label]) => ({ value, label }))]
  }, [draftRows])

  const filteredDraftRows = useMemo(() => draftRows.filter((row) => {
    if (draftFilters.material !== 'all' && row.material_group !== draftFilters.material) return false
    if (draftFilters.scene !== 'all' && row.scene_key !== draftFilters.scene) return false
    if (draftFilters.evidence !== 'all' && row.evidence_status !== draftFilters.evidence) return false
    if (draftFilters.review !== 'all' && row.review_status !== draftFilters.review) return false
    if (summaryFilter === 'reviewed' && row.review_status !== 'reviewed') return false
    if (summaryFilter === 'attention' && !row.attention) return false
    const query = draftFilters.search.trim().toLocaleLowerCase()
    return !query || `${row.batch_label} ${row.component_type} ${row.scene_name}`.toLocaleLowerCase().includes(query)
  }), [draftFilters, draftRows, summaryFilter])

  const pageCount = Math.max(1, Math.ceil(filteredDraftRows.length / DRAFT_PAGE_SIZE))
  const safePage = Math.min(page, pageCount)
  const pagedDraftRows = filteredDraftRows.slice((safePage - 1) * DRAFT_PAGE_SIZE, safePage * DRAFT_PAGE_SIZE)

  const draftAttentionRows: W02AttentionRow[] = filteredDraftRows
    .filter((row) => row.attention)
    .map((row) => ({
      row_key: row.row_key,
      canonical_batch_id: row.canonical_batch_id,
      batch_label: row.batch_label,
      material_group: row.material_group,
      attention_reason: row.attention_reason ?? '需要进一步审查',
    }))

  const verificationCommonRows = useMemo(() => verificationRows.filter((row) => {
    if (verificationFilters.material !== 'all' && row.material_group !== verificationFilters.material) return false
    if (verificationFilters.scene !== 'all' && row.scene_key !== verificationFilters.scene) return false
    if (verificationFilters.type !== 'all' && row.verification_type !== verificationFilters.type) return false
    const query = verificationFilters.search.trim().toLocaleLowerCase()
    return !query || `${row.batch_label} ${row.field} ${row.question} ${row.scene_name}`.toLocaleLowerCase().includes(query)
  }), [verificationFilters.material, verificationFilters.scene, verificationFilters.search, verificationFilters.type, verificationRows])

  const filteredVerificationRows = useMemo(() => verificationCommonRows.filter((row) => {
    if (verificationFilters.status === 'active') return ACTIVE_VERIFICATION_STATUSES.has(row.status)
    return verificationFilters.status === 'all' || row.status === verificationFilters.status
  }), [verificationCommonRows, verificationFilters.status])

  const canonicalSummaryItemIds = new Set(
    verificationCommonRows
      .filter((row) => row.canonical_batch_id)
      .map((row) => row.row_key.replace('canonical:', '')),
  )
  const canonicalSummaryItems: VerificationItem[] = verificationItems.filter(
    (item) => canonicalSummaryItemIds.has(item.verification_id),
  )
  const verificationSummary = selectW02BSummary(
    projectId,
    assessmentBatches,
    canonicalSummaryItems,
    { scope: 'active-task-context' },
  )

  const isDefaultVerificationView =
    verificationFilters.material === 'all'
    && verificationFilters.scene === 'all'
    && verificationFilters.type === 'all'
    && verificationFilters.status === 'active'
    && verificationFilters.search.trim() === ''

  const verificationGroups = useMemo<W02MaterialGroup[]>(() => {
    const materials = isDefaultVerificationView
      ? [...new Set(draftRows.map((row) => row.material_group))]
      : [...new Set(filteredVerificationRows.map((row) => row.material_group))]
    return materials.map((material) => {
      const rows = filteredVerificationRows.filter((row) => row.material_group === material)
      const activeRows = rows.filter((row) => ACTIVE_VERIFICATION_STATUSES.has(row.status))
      return {
        material,
        rows,
        activeCount: activeRows.length,
        affectedBatchCount: new Set(activeRows.map((row) => row.group_key)).size,
      }
    })
  }, [draftRows, filteredVerificationRows, isDefaultVerificationView])

  const effectiveExpandedMaterial = verificationGroups.some((group) => group.material === expandedMaterial)
    ? expandedMaterial
    : verificationGroups.find((group) => group.activeCount > 0)?.material ?? verificationGroups[0]?.material ?? null

  const visibleCanonicalVerificationBatchIds = new Set(
    filteredVerificationRows.flatMap((row) => row.canonical_batch_id ? [row.canonical_batch_id] : []),
  )
  const verificationAttentionRows: W02AttentionRow[] = draftRows
    .filter((row) => row.attention && (
      row.canonical_batch_id
        ? visibleCanonicalVerificationBatchIds.has(row.canonical_batch_id)
        : filteredVerificationRows.some((item) => item.group_key === row.row_key)
    ))
    .map((row) => ({
      row_key: row.row_key,
      canonical_batch_id: row.canonical_batch_id,
      batch_label: row.batch_label,
      material_group: row.material_group,
      attention_reason: row.attention_reason ?? '需要进一步审查',
    }))
  function openDraftBatch(batchId: AssessmentBatchId, focusTarget?: string) {
    const context: D01NavigationContext = {
      source: 'review-draft',
      source_tab: 'review-draft',
      batch_id: batchId,
      focus_target: focusTarget,
      return_state: {
        source_tab: 'review-draft',
        summary_filter: summaryFilter,
        material_filter: draftFilters.material,
        scene_filter: draftFilters.scene,
        evidence_filter: draftFilters.evidence,
        review_filter: draftFilters.review,
        search: draftFilters.search,
        page: safePage,
        scroll_y: window.scrollY,
        focus_target: focusTarget,
      },
    }
    navigate(ImplementationRoutes.d01.replace(':batchId', encodeURIComponent(batchId)), { state: context })
  }

  function openVerificationBatch(batchId: AssessmentBatchId, focusTarget?: string) {
    const context: D01NavigationContext = {
      source: 'review-verification',
      source_tab: 'review-verification',
      batch_id: batchId,
      focus_target: focusTarget,
      return_state: {
        source_tab: 'review-verification',
        material_filter: verificationFilters.material,
        scene_filter: verificationFilters.scene,
        verification_type_filter: verificationFilters.type,
        verification_status_filter: verificationFilters.status,
        search: verificationFilters.search,
        expanded_material: effectiveExpandedMaterial,
        scroll_y: window.scrollY,
        focus_target: focusTarget,
      },
    }
    navigate(ImplementationRoutes.d01.replace(':batchId', encodeURIComponent(batchId)), { state: context })
  }

  return (
    <WorkspaceShell
      projectName={project?.name ?? '当前项目'}
      projectContextLabel={project?.region}
      items={WORKSPACE_NAVIGATION_ITEMS}
      activeDestination="review"
      onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
      headerCenter={<div className="w02-header-title">项目审查</div>}
      headerAction={(
        <Button className="workspace-context-action w02-view-entry" onClick={() => navigate(ImplementationRoutes.w01)}>
          <span>返回再生视图</span>
        </Button>
      )}
      frameClassName="w02-frame"
      contentClassName="w02-main"
    >
      <div className="w02-page-head">
        <h1>项目审查</h1>
        <div className="w02-meta">{project?.name} <span>/</span> {project?.region} <span>/</span> {w02DemoProjection.review_date}</div>
      </div>
      <W02ReviewTabs tab={tab} onChange={setTab} />

      {tab === 'draft' ? (
        <>
          <W02DraftSummary summary={draftSummary} activeFilter={summaryFilter} onFilter={(next) => { setSummaryFilter(next); setPage(1) }} />
          <div className="w02-workspace">
            <section className="w02-table-panel">
              <W02DraftToolbar filters={draftFilters} materials={materialOptions} scenes={sceneOptions} onChange={(next) => { setDraftFilters(next); setPage(1) }} />
              <W02DraftTable
                rows={pagedDraftRows}
                total={filteredDraftRows.length}
                page={safePage}
                pageCount={pageCount}
                onPage={setPage}
                onOpenBatch={openDraftBatch}
                onClear={() => { setDraftFilters(DEFAULT_DRAFT_FILTERS); setSummaryFilter('all'); setPage(1) }}
              />
            </section>
            <W02AttentionRail rows={draftAttentionRows} mode="draft" onOpen={(batchId) => openDraftBatch(batchId, 'human_verification')} />
          </div>
        </>
      ) : (
        <>
          <W02VerificationSummary summary={verificationSummary} />
          <div className="w02-workspace">
            <section className="w02-table-panel w02-v-panel">
              <W02VerificationToolbar filters={verificationFilters} materials={materialOptions} scenes={sceneOptions} onChange={setVerificationFilters} />
              <W02VerificationTable
                groups={verificationGroups}
                expandedMaterial={effectiveExpandedMaterial}
                onToggle={(material) => setExpandedMaterial(effectiveExpandedMaterial === material ? null : material)}
                onOpenBatch={openVerificationBatch}
                onClear={() => { setVerificationFilters(DEFAULT_VERIFICATION_FILTERS); setExpandedMaterial('木材') }}
              />
            </section>
            <W02AttentionRail rows={verificationAttentionRows} mode="verification" onOpen={(batchId) => openVerificationBatch(batchId, 'human_verification')} />
          </div>
        </>
      )}
    </WorkspaceShell>
  )
}
