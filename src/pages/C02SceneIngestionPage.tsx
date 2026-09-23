import { Box, FileText, Focus, Image, Lightbulb, Link2, Save, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import type { Scene } from '../domain'
import { getSceneIngestionPresentation } from '../ui/StatusPill'
import {
  Button,
  CreationShell,
  EmptyState,
  GuidanceItem,
  GuidancePanel,
  MediaFallback,
  SceneIngestionStatusPill,
} from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

export function C02SceneIngestionPage() {
  return (
    <CreationShell activeStep={2}>
      <ProjectSessionGate><C02SceneIngestionContent /></ProjectSessionGate>
    </CreationShell>
  )
}

function C02SceneIngestionContent() {
  const navigate = useNavigate()
  const { project, scenes } = useProjectSession()
  const receivedCount = scenes.filter((scene) => scene.ingestion_status === 'received').length
  const presentationSceneCount = scenes.length + 1

  return (
    <div className="creation-layout">
      <section className="panel creation-main-panel ingestion-main">
        <h1 className="page-title">现场素材接入</h1>
        <p className="page-description">来自现场采集的 360° 素材将自动进入当前项目，并作为后续构件识别与再生评估的输入。</p>
        <section className="ingestion-connection" aria-label="素材接入状态">
          <div className="ingestion-connection__icon"><Link2 size={45} /><span /></div>
          <div>
            <div className="ingestion-eyebrow"><span />现场采集通道已连接</div>
            <h2>正在接收现场素材</h2>
            <p>来自 Insta360 的新素材会自动进入当前项目；新的场景会在下方列表中出现。</p>
            <div className="ingestion-meta">
              <span>当前项目 <strong>{project?.name}</strong></span>
              <i aria-hidden="true" />
              <span>已接入 {presentationSceneCount} 个场景</span>
            </div>
          </div>
        </section>
        <div className="section-heading">
          <h2>已接入场景</h2>
          <span>{presentationSceneCount} 已接入</span>
        </div>
        {scenes.length === 0 ? (
          <EmptyState title="暂无场景" description="新接入的场景将在这里显示。" />
        ) : (
          <div className="scene-grid">
            {scenes.map((scene, index) => <SceneCard key={scene.scene_id} scene={scene} index={index + 1} />)}
            <PresentationSceneCard index={presentationSceneCount} />
          </div>
        )}
        <p className="ingestion-note">黑客松原型：场景媒体使用中性占位，不复原真实照片；点击场景名称可重命名。</p>
        <div className="page-actions page-actions--split">
          <Button variant="secondary" onClick={() => navigate(ImplementationRoutes.c01)}>返回上一步</Button>
          <Button disabled={receivedCount === 0} onClick={() => navigate(ImplementationRoutes.c03)}>开始分析</Button>
        </div>
      </section>
      <aside className="creation-aside">
        <GuidancePanel title="采集建议">
          <GuidanceItem icon={Image} title="覆盖主要空间与构件区域">尽量采集项目中具有代表性的空间与关键构件区域。</GuidanceItem>
          <GuidanceItem icon={Focus} title="保证关键构件有清晰视角">对需要评估的建筑构件尽量保留清晰、完整的视角。</GuidanceItem>
          <GuidanceItem icon={Box} title="兼顾整体环境与关键细节">既保留空间上下文，也覆盖可能影响后续判断的关键部位。</GuidanceItem>
          <GuidanceItem icon={FileText} title="必要时补充关键位置">发现特殊构件或遮挡位置时，可额外补拍对应区域。</GuidanceItem>
        </GuidancePanel>
        <section className="panel guidance-panel mini-tip-panel">
          <span className="guidance-icon guidance-icon--accent"><Lightbulb size={25} /></span>
          <div><h2>小提示</h2><p>素材接入后，系统将进入构件识别、分组与初步再生评估流程。</p></div>
        </section>
      </aside>
    </div>
  )
}

/** v2.4 composition-only row; it is intentionally not a canonical Scene. */
function PresentationSceneCard({ index }: { index: number }) {
  return (
    <article className="scene-card" data-authority="demo-only">
      <MediaFallback label="后勤区 媒体占位" />
      <div className="scene-card__content">
        <div className="scene-card__name"><strong>场景 {String(index).padStart(2, '0')}　后勤区</strong></div>
        <SceneIngestionStatusPill status="received" />
        <small>360° 场景 · 已接入</small>
      </div>
    </article>
  )
}

function SceneCard({ scene, index }: { scene: Scene; index: number }) {
  const { renameScene } = useProjectSession()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(scene.name)

  async function save() {
    const trimmed = name.trim()
    if (!trimmed) {
      setName(scene.name)
      setEditing(false)
      return
    }
    try {
      await renameScene(scene.scene_id, trimmed)
      setEditing(false)
    } catch {
      setName(scene.name)
    }
  }

  return (
    <article className="scene-card">
      <MediaFallback label={`${scene.name} 媒体占位`} />
      <div className="scene-card__content">
        <div className="scene-card__name">
          {editing ? (
            <>
              <input aria-label={`场景 ${index} 名称`} value={name} onChange={(event) => setName(event.target.value)} />
              <button type="button" aria-label="保存场景名称" onClick={save}><Save size={17} /></button>
              <button type="button" aria-label="取消重命名" onClick={() => { setName(scene.name); setEditing(false) }}><X size={17} /></button>
            </>
          ) : (
            <>
              <button className="scene-card__rename" type="button" aria-label={`重命名 ${scene.name}`} onClick={() => setEditing(true)}>
                场景 {String(index).padStart(2, '0')}　{scene.name}
              </button>
            </>
          )}
        </div>
        <SceneIngestionStatusPill status={scene.ingestion_status} />
        <small>360° 场景 · {getSceneIngestionPresentation(scene.ingestion_status).label}</small>
      </div>
    </article>
  )
}
