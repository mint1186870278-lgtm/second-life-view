import { ChevronRight, Info, Leaf, Minus, Plus } from 'lucide-react'
import type { W01ViewerMode } from '../../navigation'
import type {
  W01DemoProjection,
  W01FilmstripItem,
  W01HotspotReadModel,
  W01TaskReadModel,
} from '../../selectors'

function TaskListIcon() {
  return <svg className="w01-card-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="4" y="5" width="16" height="14" rx="2" /><path d="M8 9h8M8 13h8M8 17h5" /></svg>
}

function HotspotLayer({
  sceneId,
  hotspots,
  projection,
  onOpenBatch,
}: {
  sceneId: string
  hotspots: readonly W01HotspotReadModel[]
  projection: W01DemoProjection
  onOpenBatch: (batchId: string) => void
}) {
  const canonicalByBatch = new Map(hotspots.map((hotspot) => [hotspot.batch_id, hotspot]))
  const rows = projection.hotspot_rows.filter((row) => row.scene_id === sceneId)
  return (
    <div className="w01-hotspot-layer" aria-label="评估热点">
      {rows.map((row) => {
        const canonical = row.batch_id ? canonicalByBatch.get(row.batch_id) : undefined
        const content = <>
          <span className={`w01-hotspot-marker is-${row.tone}`} aria-hidden="true" />
          <span className="w01-hotspot-pill">
            <span>{row.label}</span>
            <small>× {row.quantity}</small>
            <ChevronRight size={15} />
          </span>
        </>
        const style = { left: `${row.x_percent}%`, top: `${row.y_percent}%` }
        return canonical ? (
          <button
            className="w01-hotspot"
            type="button"
            key={row.presentation_id}
            style={style}
            onClick={() => onOpenBatch(canonical.batch_id)}
            aria-label={`查看 ${row.label} 详情`}
            data-batch-id={canonical.batch_id}
          >{content}</button>
        ) : (
          <div className="w01-hotspot" key={row.presentation_id} style={style} data-authority="demo-only">{content}</div>
        )
      })}
    </div>
  )
}

function ViewerControls({
  zoom,
  minZoom,
  maxZoom,
  onZoomIn,
  onZoomOut,
}: {
  zoom: number
  minZoom: number
  maxZoom: number
  onZoomIn: () => void
  onZoomOut: () => void
}) {
  return (
    <div className="w01-viewer-controls">
      <div className="w01-orientation" aria-label="当前朝向 北">
        <span aria-hidden="true" />
        <strong>N</strong>
      </div>
      <div className="w01-zoom-controls" role="group" aria-label="缩放控制">
        <button type="button" aria-label="放大" onClick={onZoomIn} disabled={zoom >= maxZoom}>
          <Plus size={21} />
        </button>
        <button type="button" aria-label="缩小" onClick={onZoomOut} disabled={zoom <= minZoom}>
          <Minus size={21} />
        </button>
      </div>
      <output className="sr-only" aria-label="当前缩放">{Math.round(zoom * 100)}%</output>
    </div>
  )
}

function ContextTaskCard({
  tasks,
  projection,
  onOpenTask,
}: {
  tasks: readonly W01TaskReadModel[]
  projection: W01DemoProjection
  onOpenTask: (task: W01TaskReadModel) => void
}) {
  return (
    <section className="w01-overlay-card" aria-labelledby="w01-task-title">
      <h2 id="w01-task-title"><TaskListIcon />待处理事项</h2>
      <div className="w01-task-list">
        {projection.task_rows.map((row) => {
          const task = tasks.find((item) => item.focus_target === row.focus_target)
          const content = <>
            <span className={`w01-task-dot is-${row.tone}`} />
            <span>{row.label}</span>
            <ChevronRight size={16} />
          </>
          return task ? (
            <button className="w01-task-row" type="button" key={row.label} onClick={() => onOpenTask(task)}>{content}</button>
          ) : (
            <div className="w01-task-row" key={row.label} data-authority="demo-only">{content}</div>
          )
        })}
      </div>
    </section>
  )
}

function AssessmentInfoCard() {
  return (
    <section className="w01-overlay-card" aria-labelledby="w01-assessment-title">
      <h2 id="w01-assessment-title"><Info size={19} />评估说明</h2>
      <p className="w01-assessment-copy">当前结果基于现场素材自动识别与初步判断生成。<br /><br />关键构件状态、证据不足或与建议路径需由人工进一步核实。</p>
    </section>
  )
}

function RegenerationPotentialCard({ projection }: { projection: W01DemoProjection['potential'] }) {
  return (
    <section className="w01-potential-card" aria-label="再生潜力" data-authority="demo-only">
      <span className="w01-potential-icon"><Leaf size={27} /></span>
      <div>
        <h2>再生潜力</h2>
        <p>{projection.value} {projection.copy}</p>
      </div>
    </section>
  )
}

export function SceneViewer({
  scene,
  mode,
  zoom,
  minZoom,
  maxZoom,
  hotspots,
  tasks,
  demoProjection,
  onZoomIn,
  onZoomOut,
  onOpenBatch,
  onOpenTask,
}: {
  scene: W01FilmstripItem
  mode: W01ViewerMode
  zoom: number
  minZoom: number
  maxZoom: number
  hotspots: readonly W01HotspotReadModel[]
  tasks: readonly W01TaskReadModel[]
  demoProjection: W01DemoProjection
  onZoomIn: () => void
  onZoomOut: () => void
  onOpenBatch: (batchId: string) => void
  onOpenTask: (task: W01TaskReadModel) => void
}) {
  const regeneration = mode === 'regeneration'
  return (
    <section className={`w01-viewer is-tone-${scene.visual_tone}`} aria-labelledby="w01-page-title" data-scene-id={scene.scene_id}>
      <div className="w01-scene-layer" style={{ transform: `scale(${zoom})` }}>
        <div className="w01-panorama" role="img" aria-label={`${scene.name} 360° 场景视觉占位`} />
        {regeneration && <HotspotLayer sceneId={scene.scene_id} hotspots={hotspots} projection={demoProjection} onOpenBatch={onOpenBatch} />}
      </div>
      <h1 className="sr-only" id="w01-page-title">再生视图</h1>
      <div className="w01-overlay-rail">
        <ViewerControls zoom={zoom} minZoom={minZoom} maxZoom={maxZoom} onZoomIn={onZoomIn} onZoomOut={onZoomOut} />
        {regeneration && <div className="w01-overlay-stack">
          <ContextTaskCard tasks={tasks} projection={demoProjection} onOpenTask={onOpenTask} />
          <AssessmentInfoCard />
        </div>}
      </div>
      {regeneration && <RegenerationPotentialCard projection={demoProjection.potential} />}
    </section>
  )
}

export function SceneFilmstrip({
  scenes,
  fillers,
  selectedSceneId,
  onSelect,
}: {
  scenes: readonly W01FilmstripItem[]
  fillers: W01DemoProjection['filmstrip_fillers']
  selectedSceneId: string
  onSelect: (sceneId: string) => void
}) {
  return (
    <section className="w01-filmstrip" aria-label="场景胶片栏">
      {scenes.map((scene, index) => (
        <button
          type="button"
          className={`w01-filmstrip-item is-tone-${scene.visual_tone}`}
          key={scene.scene_id}
          aria-pressed={scene.scene_id === selectedSceneId}
          onClick={() => onSelect(scene.scene_id)}
        >
          <span className="w01-filmstrip-media" aria-hidden="true" />
          <span className="w01-filmstrip-caption">
            <small>场景 {String(index + 1).padStart(2, '0')}</small>
            <strong>{scene.name}</strong>
          </span>
        </button>
      ))}
      {fillers.map((scene, index) => (
        <div className={`w01-filmstrip-item is-tone-${scene.tone}`} key={scene.label} data-authority="demo-only">
          <span className="w01-filmstrip-media" aria-hidden="true" />
          <span className="w01-filmstrip-caption">
            <small>场景 {String(scenes.length + index + 1).padStart(2, '0')}</small>
            <strong>{scene.label}</strong>
          </span>
        </div>
      ))}
    </section>
  )
}
