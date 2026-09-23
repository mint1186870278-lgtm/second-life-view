import { Box, Check, FileText, Focus, Image, Lightbulb, Link2, LoaderCircle } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { DemoScene } from '../api/demo'
import { useCreationFlow } from '../app/CreationFlowContext'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { Button, CreationShell, EmptyState, GuidanceItem, GuidancePanel } from '../ui'
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
  const { project } = useProjectSession()
  const {
    demoScenes,
    selectedSceneIds,
    sceneCatalogStatus,
    sceneCatalogError,
    analysisStatus,
    analysisError,
    spatialPrompt,
    setSpatialPrompt,
    loadDemoScenes,
    toggleDemoScene,
    setAllDemoScenesSelected,
    startDemoAnalysis,
  } = useCreationFlow()

  useEffect(() => {
    void loadDemoScenes()
  }, [loadDemoScenes])

  const selectedScenes = demoScenes.filter((scene) => selectedSceneIds.includes(scene.id))
  const detectionCount = selectedScenes.reduce((total, scene) => total + scene.detection_count, 0)
  const groupCount = selectedScenes.reduce((total, scene) => total + scene.group_count, 0)
  const isAnalyzing = analysisStatus === 'running'

  const handleAnalyze = async () => {
    try {
      await startDemoAnalysis()
      navigate(ImplementationRoutes.c03)
    } catch {
      // CreationFlowContext exposes the actionable error beside the button.
    }
  }

  return (
    <div className="creation-layout">
      <section className="panel creation-main-panel ingestion-main">
        <h1 className="page-title">现场素材接入</h1>
        <p className="page-description">当前以仓库内 360° 样例图模拟 Insta360 SDK 推流；后续替换素材入口即可复用同一分析链路。</p>
        <section className="ingestion-connection" aria-label="素材接入状态">
          <div className="ingestion-connection__icon"><Link2 size={45} /><span /></div>
          <div>
            <div className="ingestion-eyebrow"><span />Insta360 模拟采集通道已连接</div>
            <h2>样例素材已进入当前项目</h2>
            <p>图片来自 <code>data/samples/pictures</code>，并带有 YOLO-World 跨视角检测缓存，可直接构成端到端 Demo。</p>
            <div className="ingestion-meta">
              <span>当前项目 <strong>{project?.name}</strong></span>
              <i aria-hidden="true" />
              <span>已选择 <strong>{selectedScenes.length}</strong> / {demoScenes.length} 个场景</span>
              <i aria-hidden="true" />
              <span>{detectionCount} 个检测框 → {groupCount} 个构件组</span>
            </div>
          </div>
        </section>

        <div className="section-heading scene-heading">
          <div><h2>现场素材</h2><span>点击卡片选择本次分析输入</span></div>
          <div className="scene-selection-actions">
            <button type="button" onClick={() => setAllDemoScenesSelected(true)}>全选</button>
            <button type="button" onClick={() => setAllDemoScenesSelected(false)}>清空</button>
          </div>
        </div>

        {sceneCatalogStatus === 'loading' && demoScenes.length === 0 ? (
          <div className="ingestion-loading"><LoaderCircle className="spin" size={24} />正在读取本地全景素材…</div>
        ) : demoScenes.length === 0 ? (
          <EmptyState title="暂无场景" description="请确认后端可访问 data/samples/pictures。" />
        ) : (
          <div className="scene-grid scene-grid--media">
            {demoScenes.map((scene, index) => (
              <DemoSceneCard
                key={scene.id}
                scene={scene}
                index={index + 1}
                selected={selectedSceneIds.includes(scene.id)}
                onToggle={() => toggleDemoScene(scene.id)}
              />
            ))}
          </div>
        )}

        {sceneCatalogStatus === 'fallback' && (
          <p className="inline-notice inline-notice--warning">素材接口暂不可用，当前显示本地清单；启动 FastAPI 后即可执行完整分析。{sceneCatalogError ? ` ${sceneCatalogError}` : ''}</p>
        )}

        <label className="spatial-prompt-field">
          <span>Aholo AI 空间改造提示</span>
          <textarea value={spatialPrompt} onChange={(event) => setSpatialPrompt(event.target.value)} rows={2} />
        </label>

        {analysisError && <p className="inline-notice inline-notice--error" role="alert">{analysisError}</p>}
        <div className="page-actions page-actions--split">
          <Button variant="secondary" onClick={() => navigate(ImplementationRoutes.c01)}>返回上一步</Button>
          <Button disabled={!selectedSceneIds.length || isAnalyzing} onClick={handleAnalyze}>
            {isAnalyzing ? <><LoaderCircle className="spin" size={18} />Agent 分析中…</> : '开始全链路分析'}
          </Button>
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

function DemoSceneCard({ scene, index, selected, onToggle }: { scene: DemoScene; index: number; selected: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      className={`scene-card scene-card--selectable ${selected ? 'is-selected' : ''}`}
      aria-pressed={selected}
      aria-label={`${selected ? '取消选择' : '选择'} ${scene.name}`}
      onClick={onToggle}
    >
      <span className="scene-card__media">
        <img src={scene.thumbnail_url} alt={`${scene.name} 360° 全景`} loading="lazy" />
        <span className="scene-card__check"><Check size={15} /></span>
      </span>
      <span className="scene-card__content">
        <span className="scene-card__name"><strong>场景 {String(index).padStart(2, '0')}　{scene.name}</strong></span>
        <span className="scene-card__badges"><em>360° 已接入</em><em>YOLO {scene.group_count} 组</em></span>
        <small>{scene.width}×{scene.height} · {scene.detection_count} 个原始检测框</small>
      </span>
    </button>
  )
}
