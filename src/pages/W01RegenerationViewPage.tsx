import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import {
  getWorkspaceDestinationRoute,
  WORKSPACE_NAVIGATION_ITEMS,
} from '../app/workspaceNavigation'
import { w01DemoProjection } from '../config'
import type { AssessmentBatchId, SceneId } from '../domain'
import type { D01NavigationContext, W01ViewerMode } from '../navigation'
import { selectW01SceneReadModel, type W01TaskReadModel } from '../selectors'
import { Button, EmptyState, WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'
import { ViewerModeSwitch, W01SidebarSupplement } from './w01/W01Chrome'
import { SceneFilmstrip, SceneViewer } from './w01/W01Viewer'

const W01_ZOOM_MIN = 1
const W01_ZOOM_MAX = 2.2
const W01_ZOOM_STEP = 0.15

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
  const navigate = useNavigate()
  const [selectedSceneId, setSelectedSceneId] = useState<SceneId | undefined>(scenes[0]?.scene_id)
  const [viewerMode, setViewerMode] = useState<W01ViewerMode>('regeneration')
  const [zoom, setZoom] = useState(W01_ZOOM_MIN)

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

  if (!readModel.selected_scene) {
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

  const selectedFilmstripItem = readModel.filmstrip.find(
    (scene) => scene.scene_id === readModel.selected_scene?.scene_id,
  )!

  return (
    <WorkspaceShell
      projectName={`${project?.name ?? '当前项目'} · ${readModel.selected_scene.name}`}
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
        hotspots={readModel.hotspots}
        tasks={readModel.tasks}
        demoProjection={w01DemoProjection}
        onZoomIn={() => setZoom((value) => Math.min(W01_ZOOM_MAX, Number((value + W01_ZOOM_STEP).toFixed(2))))}
        onZoomOut={() => setZoom((value) => Math.max(W01_ZOOM_MIN, Number((value - W01_ZOOM_STEP).toFixed(2))))}
        onOpenBatch={(batchId) => openD01(batchId)}
        onOpenTask={(task: W01TaskReadModel) => openD01(task.batch_id, task.focus_target)}
      />
      <SceneFilmstrip
        scenes={readModel.filmstrip}
        fillers={w01DemoProjection.filmstrip_fillers}
        selectedSceneId={readModel.selected_scene.scene_id}
        onSelect={selectScene}
      />
    </WorkspaceShell>
  )
}
