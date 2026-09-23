import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { DemoAnalysisResult, DemoGroup } from '../api/demo'
import { useCreationFlow } from '../app/CreationFlowContext'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import {
  getWorkspaceDestinationRoute,
  WORKSPACE_NAVIGATION_ITEMS,
} from '../app/workspaceNavigation'
import { w01DemoProjection, w01DemoSceneAssetUrls } from '../config'
import type { AssessmentBatchId, SceneId } from '../domain'
import type { D01NavigationContext, W01ViewerMode } from '../navigation'
import {
  selectW01SceneReadModel,
  type W01AnnotationGroup,
  type W01DemoGroupRow,
  type W01FilmstripItem,
  type W01TaskReadModel,
} from '../selectors'
import { Button, EmptyState, WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'
import { ViewerModeSwitch, W01SidebarSupplement } from './w01/W01Chrome'
import { SceneFilmstrip, SceneViewer } from './w01/W01Viewer'

const W01_ZOOM_MIN = 1
const W01_ZOOM_MAX = 2.2
const W01_ZOOM_STEP = 0.15
const AHOLO_EDITOR_URL = 'https://studio.aholo3d.cn/editor?projectId=3FO4K4XJJ82N'

const categoryNames: Record<string, string> = {
  cabinet: '柜体',
  chair: '座椅',
  door: '门',
  sofa: '沙发',
  table: '桌台',
  window: '窗',
}

export function W01RegenerationViewPage() {
  return <ProjectSessionGate><W01RegenerationViewContent /></ProjectSessionGate>
}

function W01RegenerationViewContent() {
  const {
    project,
    scenes,
    componentInstances,
    assessmentBatches,
    verificationItems,
  } = useProjectSession()
  const { analysisResult } = useCreationFlow()
  const navigate = useNavigate()
  const [selectedSceneId, setSelectedSceneId] = useState<SceneId>()
  const [viewerMode, setViewerMode] = useState<W01ViewerMode>('regeneration')
  const [zoom, setZoom] = useState(W01_ZOOM_MIN)
  const [isThreeDModalOpen, setIsThreeDModalOpen] = useState(false)

  const readModel = useMemo(() => selectW01SceneReadModel(
    project!.project_id,
    selectedSceneId,
    scenes,
    componentInstances,
    assessmentBatches,
    verificationItems,
    w01DemoProjection.hotspot_placements,
  ), [
    assessmentBatches,
    componentInstances,
    project,
    scenes,
    selectedSceneId,
    verificationItems,
  ])

  const analysisFilmstrip = useMemo(
    () => analysisResult ? buildAnalysisFilmstrip(analysisResult) : [],
    [analysisResult],
  )
  const hasAnalysisProjection = analysisFilmstrip.length > 0
  const fallbackFilmstrip = useMemo(() => readModel.filmstrip.map((scene) => ({
    ...scene,
    image_url: w01DemoSceneAssetUrls[scene.scene_id],
  })), [readModel.filmstrip])
  const filmstrip = hasAnalysisProjection ? analysisFilmstrip : fallbackFilmstrip
  const sceneIdsKey = filmstrip.map((scene) => scene.scene_id).join('|')

  useEffect(() => {
    setSelectedSceneId((current) => filmstrip.some((scene) => scene.scene_id === current) ? current : filmstrip[0]?.scene_id)
    setZoom(W01_ZOOM_MIN)
  }, [sceneIdsKey])

  const selectedFilmstripItem = filmstrip.find((scene) => scene.scene_id === selectedSceneId) ?? filmstrip[0]
  const analysisGroupRows = useMemo(
    () => analysisResult ? buildSidebarGroupRows(analysisResult.groups, analysisResult.group_count) : undefined,
    [analysisResult],
  )

  function openD01(batchId: AssessmentBatchId, focusTarget?: string) {
    if (!readModel.selected_scene) return
    const context: D01NavigationContext = {
      source: 'view',
      batch_id: batchId,
      focus_target: focusTarget,
      return_state: {
        scene_id: readModel.selected_scene.scene_id,
        viewer_mode: viewerMode,
        zoom_level: zoom,
        scroll_y: window.scrollY,
        focus_target: focusTarget,
      },
    }
    navigate(ImplementationRoutes.d01.replace(':batchId', encodeURIComponent(batchId)), { state: context })
  }

  function selectScene(sceneId: SceneId) {
    setSelectedSceneId(sceneId)
    setZoom(W01_ZOOM_MIN)
  }

  if (!selectedFilmstripItem) {
    return (
      <WorkspaceShell
        projectName={project?.name ?? '当前项目'}
        projectContextLabel={project?.region}
        items={WORKSPACE_NAVIGATION_ITEMS}
        activeDestination="view"
        onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
      >
        <EmptyState title="暂无场景" description="接入至少一个场景后即可使用再生视图。" />
      </WorkspaceShell>
    )
  }

  return (
    <>
      <WorkspaceShell
        projectName={`${project?.name ?? '当前项目'} · ${selectedFilmstripItem.name}`}
        projectContextLabel={project?.region}
        items={WORKSPACE_NAVIGATION_ITEMS}
        activeDestination="view"
        onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
        headerCenter={<ViewerModeSwitch mode={viewerMode} onChange={setViewerMode} />}
        headerAction={(
          <Button className="w01-review-entry" onClick={() => navigate(ImplementationRoutes.w02)}>
            <span>进入项目审查</span>
          </Button>
        )}
        sidebarSupplement={(
          <W01SidebarSupplement
            demoProjection={w01DemoProjection}
            componentCount={hasAnalysisProjection ? analysisResult?.component_count : undefined}
            groupCount={hasAnalysisProjection ? analysisResult?.group_count : undefined}
            groupRows={analysisGroupRows}
            summaryRows={hasAnalysisProjection ? [] : w01DemoProjection.coarse_summary}
            isDemoProjection={!hasAnalysisProjection}
          />
        )}
        contentClassName="w01-content"
      >
        <SceneViewer
          scene={selectedFilmstripItem}
          mode={viewerMode}
          zoom={zoom}
          minZoom={W01_ZOOM_MIN}
          maxZoom={W01_ZOOM_MAX}
          hotspots={hasAnalysisProjection ? [] : readModel.hotspots}
          tasks={hasAnalysisProjection ? [] : readModel.tasks}
          demoProjection={w01DemoProjection}
          onZoomIn={() => setZoom((value) => Math.min(W01_ZOOM_MAX, Number((value + W01_ZOOM_STEP).toFixed(2))))}
          onZoomOut={() => setZoom((value) => Math.max(W01_ZOOM_MIN, Number((value - W01_ZOOM_STEP).toFixed(2))))}
          onOpenBatch={(batchId) => openD01(batchId)}
          onOpenTask={(task: W01TaskReadModel) => openD01(task.batch_id, task.focus_target)}
          onOpenThreeD={() => setIsThreeDModalOpen(true)}
        />
        <SceneFilmstrip
          scenes={filmstrip}
          fillers={hasAnalysisProjection ? [] : w01DemoProjection.filmstrip_fillers}
          selectedSceneId={selectedFilmstripItem.scene_id}
          onSelect={selectScene}
        />
      </WorkspaceShell>
      {isThreeDModalOpen && <ThreeDRegenerationDialog onClose={() => setIsThreeDModalOpen(false)} />}
    </>
  )
}

function buildAnalysisFilmstrip(result: DemoAnalysisResult): W01FilmstripItem[] {
  const groupsByScene = new Map<string, DemoGroup[]>()
  result.groups.forEach((group) => {
    const groups = groupsByScene.get(group.scene_id) ?? []
    groups.push(group)
    groupsByScene.set(group.scene_id, groups)
  })

  return result.scenes.map((scene, sceneIndex) => ({
    scene_id: scene.id,
    name: scene.name,
    ingestion_status: 'received',
    visual_tone: sceneIndex % 4,
    image_url: scene.asset_url,
    annotated_image_url: scene.annotated_url,
    annotation_groups: buildAnnotationGroups(
      (groupsByScene.get(scene.id) ?? []).filter((group) => group.confidence >= 0.2),
    ),
  }))
}

function buildAnnotationGroups(groups: readonly DemoGroup[]): W01AnnotationGroup[] {
  const categoryOrdinals = new Map<string, number>()
  return [...groups]
    .sort((left, right) => right.confidence - left.confidence)
    .map((group) => {
      const ordinal = (categoryOrdinals.get(group.category) ?? 0) + 1
      categoryOrdinals.set(group.category, ordinal)
      return {
        id: group.id,
        name: group.group_name ?? `${categoryNames[group.category] ?? group.label}组 ${String(ordinal).padStart(2, '0')}`,
        category: group.category,
        quantity: group.detected_count,
      }
    })
}

function buildSidebarGroupRows(groups: readonly DemoGroup[], groupCount: number): W01DemoGroupRow[] {
  const rows = buildAnnotationGroups(groups).slice(0, 7).map((group) => ({
    label: group.name,
    quantity_label: `× ${group.quantity}`,
    tone: group.category,
  }))
  const hiddenCount = Math.max(0, groupCount - rows.length)
  return hiddenCount > 0
    ? [...rows, { label: '其余构件组', quantity_label: `+ ${hiddenCount}`, tone: 'more' }]
    : rows
}

function ThreeDRegenerationDialog({ onClose }: { onClose: () => void }) {
  return (
    <div className="w01-3d-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="w01-3d-modal" role="dialog" aria-modal="true" aria-labelledby="w01-3d-modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <button type="button" className="w01-3d-modal__close" aria-label="关闭 3D再生" onClick={onClose}>×</button>
        <span className="w01-3d-modal__eyebrow">AHOLO</span>
        <h2 id="w01-3d-modal-title">3D再生</h2>
        <p>当前场景可在 Aholo Studio 中继续进行 3D 再生与空间编辑。</p>
        <a href={AHOLO_EDITOR_URL} target="_blank" rel="noreferrer">{AHOLO_EDITOR_URL}</a>
      </section>
    </div>
  )
}
