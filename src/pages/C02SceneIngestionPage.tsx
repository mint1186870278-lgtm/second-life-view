import { Box, Check, Camera, FileText, Focus, Image, Lightbulb, Link2, LoaderCircle, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchCaptureBridgeHealth,
  startCaptureImport,
  type CaptureBridgeResult,
} from '../api/captureBridge'
import { useCreationFlow, type LiveScene } from '../app/CreationFlowContext'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { Button, CreationShell, EmptyState, GuidanceItem, GuidancePanel } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

type CapturePhase = 'idle' | 'checking' | 'capturing' | 'ready' | 'error'

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
    projectDraft,
    demoScenes,
    liveScenes,
    selectedSceneIds,
    selectedLiveIds,
    sceneCatalogStatus,
    sceneCatalogError,
    analysisStatus,
    analysisError,
    spatialPrompt,
    setSpatialPrompt,
    loadDemoScenes,
    toggleDemoScene,
    toggleLiveScene,
    setAllScenesSelected,
    clearSceneSelection,
    addLiveScene,
    startDemoAnalysis,
  } = useCreationFlow()

  const [capturePhase, setCapturePhase] = useState<CapturePhase>('idle')
  const [captureError, setCaptureError] = useState<string>()
  const [captureResult, setCaptureResult] = useState<CaptureBridgeResult | null>(null)
  const [spaceName, setSpaceName] = useState('')
  const [confirmError, setConfirmError] = useState<string>()

  useEffect(() => {
    void loadDemoScenes()
  }, [loadDemoScenes])

  const runCapture = useCallback(async () => {
    setCaptureError(undefined)
    setConfirmError(undefined)
    setCapturePhase('checking')
    try {
      const health = await fetchCaptureBridgeHealth()
      if (!health.ok) {
        throw new Error(health.detail || '采集服务未就绪')
      }
      setCapturePhase('capturing')
      const label = spaceName.trim() || projectDraft.name || project?.name || '现场空间'
      const result = await startCaptureImport({
        project_id: project?.project_id ?? 'proj_local',
        scene_label: label,
      })
      setCaptureResult(result)
      if (!spaceName.trim()) {
        const nextIndex = liveScenes.length + 1
        setSpaceName(`现场空间 ${String(nextIndex).padStart(2, '0')}`)
      }
      setCapturePhase('ready')
    } catch (error) {
      const message = error instanceof Error ? error.message : '现场采集失败'
      const offlineHint = /Failed to fetch|NetworkError|fetch|超时|timeout|ECONNREFUSED/i.test(message)
        ? '无法连接本机采集服务。请先启动：CAPTURE_BRIDGE_BACKEND=demo_auto 后运行 python -m capture_bridge（端口 18765）。'
        : message
      setCaptureError(offlineHint)
      setCapturePhase('error')
    }
  }, [liveScenes.length, project?.name, project?.project_id, projectDraft.name, spaceName])

  const handleConfirm = () => {
    if (!captureResult?.preview_url) {
      setConfirmError('请先完成现场采集')
      return
    }
    const name = spaceName.trim()
    if (!name) {
      setConfirmError('请填写空间名称')
      return
    }
    const scene: LiveScene = {
      id: `live_${captureResult.capture_id}`,
      name,
      thumbnail_url: captureResult.preview_url,
      width: captureResult.width ?? 0,
      height: captureResult.height ?? 0,
      file_size_bytes: captureResult.file_size_bytes ?? undefined,
      capture_id: captureResult.capture_id,
      local_path: captureResult.local_path,
      source: 'live_capture',
    }
    addLiveScene(scene)
    setCaptureResult(null)
    setSpaceName('')
    setConfirmError(undefined)
    setCapturePhase('idle')
  }

  const galleryItems = useMemo(() => {
    const liveItems = liveScenes.map((scene, index) => ({
      kind: 'live' as const,
      id: scene.id,
      name: scene.name,
      index: index + 1,
      thumbnail_url: scene.thumbnail_url,
      width: scene.width,
      height: scene.height,
      selected: selectedLiveIds.includes(scene.id),
      badgePrimary: '现场实拍',
      badgeSecondary: '360° 已接入',
      meta: `${scene.width}×${scene.height}`,
      onToggle: () => toggleLiveScene(scene.id),
    }))
    const demoItems = demoScenes.map((scene, index) => ({
      kind: 'demo' as const,
      id: scene.id,
      name: scene.name,
      index: liveScenes.length + index + 1,
      thumbnail_url: scene.thumbnail_url,
      width: scene.width,
      height: scene.height,
      selected: selectedSceneIds.includes(scene.id),
      badgePrimary: '360° 已接入',
      badgeSecondary: `YOLO ${scene.group_count} 组`,
      meta: `${scene.width}×${scene.height} · ${scene.detection_count} 个原始检测框`,
      onToggle: () => toggleDemoScene(scene.id),
    }))
    return [...liveItems, ...demoItems]
  }, [demoScenes, liveScenes, selectedLiveIds, selectedSceneIds, toggleDemoScene, toggleLiveScene])

  const selectedTotal = selectedSceneIds.length + selectedLiveIds.length
  const isAnalyzing = analysisStatus === 'running'
  const isCapturing = capturePhase === 'checking' || capturePhase === 'capturing'

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
        <p className="page-description">
          点击采集框内按钮调用本机 Insta360 服务拍照下载；确认后实拍会出现在下方素材列表，可与样例一并选择进入后续流程。
        </p>

        <section className={`ingestion-connection ingestion-connection--capture ${capturePhase === 'ready' ? 'is-ready' : ''}`} aria-label="CameraSDKDemo 现场采集">
          {(capturePhase === 'idle' || capturePhase === 'error') && (
            <div className="ingestion-capture-idle">
              <div className="ingestion-connection__icon">
                <Camera size={45} />
              </div>
              <div className="ingestion-capture-idle__body">
                <div className={`ingestion-eyebrow ${capturePhase === 'error' ? 'ingestion-eyebrow--error' : 'ingestion-eyebrow--pending'}`}>
                  {capturePhase === 'error' ? '现场采集未成功' : ''}
                </div>
                <h2>{capturePhase === 'error' ? '请检查后重新采集' : '现场全景采集'}</h2>
                <p>
                  {capturePhase === 'error'
                    ? captureError
                    : '请先启动本机 capture_bridge（demo_auto），相机 USB 选安卓模式并开启机内照片拼接。'}
                </p>
                <div className="ingestion-capture-idle__actions">
                  <Button type="button" disabled={isCapturing} onClick={() => void runCapture()}>
                    采集现场照片
                  </Button>
                  <span className="ingestion-meta-inline">当前项目 <strong>{project?.name}</strong></span>
                </div>
              </div>
            </div>
          )}

          {isCapturing && (
            <div className="ingestion-capture-busy">
              <div className="ingestion-connection__icon">
                <LoaderCircle className="spin" size={45} />
              </div>
              <div>
                <div className="ingestion-eyebrow ingestion-eyebrow--pending">已连接insta全景相机...</div>
                <h2>正在现场采集…</h2>
                <p>请勿拔线；过程可能需要 30–120 秒。完成后可在本框预览并填写空间名称。</p>
                <div className="ingestion-meta">
                  <span>当前项目 <strong>{project?.name}</strong></span>
                  <i aria-hidden="true" />
                  <span>采集状态 <strong>{capturePhase === 'checking' ? '检查服务' : '拍照下载中'}</strong></span>
                </div>
              </div>
            </div>
          )}

          {capturePhase === 'ready' && captureResult && (
            <div className="ingestion-capture-ready">
              <div className="ingestion-capture-ready__preview">
                {captureResult.preview_url ? (
                  <img src={captureResult.preview_url} alt="现场采集全景预览" />
                ) : (
                  <div className="ingestion-capture-ready__placeholder">暂无预览</div>
                )}
                <div className="ingestion-capture-ready__dims">
                  {captureResult.width}×{captureResult.height}
                  {captureResult.meta?.camera_file ? ` · ${captureResult.meta.camera_file}` : ''}
                </div>
              </div>
              <div className="ingestion-capture-ready__form">
                <div className="ingestion-eyebrow"><span />现场采集完成</div>
                <h2>确认空间信息</h2>
                <label className="ingestion-space-field">
                  <span>空间名称</span>
                  <input
                    type="text"
                    value={spaceName}
                    maxLength={80}
                    placeholder="例如：屋顶花园 / 休息区"
                    onChange={(event) => {
                      setSpaceName(event.target.value)
                      setConfirmError(undefined)
                    }}
                  />
                </label>
                {confirmError ? <p className="inline-notice inline-notice--error" role="alert">{confirmError}</p> : null}
                <div className="ingestion-capture-ready__actions">
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={isCapturing}
                    onClick={() => void runCapture()}
                  >
                    <RefreshCw size={16} /> 重新采集
                  </Button>
                  <Button type="button" onClick={handleConfirm}>
                    确认
                  </Button>
                </div>
              </div>
            </div>
          )}
        </section>

        <div className="section-heading scene-heading">
          <div>
            <h2>分析用素材</h2>
            <span>现场实拍确认后会出现在此；样例场景仍可用于当前分析 Demo</span>
          </div>
          <div className="scene-selection-actions">
            <button type="button" onClick={() => setAllScenesSelected(true)}>全选</button>
            <button type="button" onClick={() => clearSceneSelection()}>清空</button>
          </div>
        </div>

        {sceneCatalogStatus === 'loading' && demoScenes.length === 0 && liveScenes.length === 0 ? (
          <div className="ingestion-loading"><LoaderCircle className="spin" size={24} />正在读取本地全景素材…</div>
        ) : galleryItems.length === 0 ? (
          <EmptyState title="暂无场景" description="请先采集并确认一张现场照片，或确认后端可访问 data/samples/pictures。" />
        ) : (
          <div className="scene-grid scene-grid--media">
            {galleryItems.map((item) => (
              <SceneCard
                key={item.id}
                index={item.index}
                name={item.name}
                thumbnailUrl={item.thumbnail_url}
                selected={item.selected}
                badgePrimary={item.badgePrimary}
                badgeSecondary={item.badgeSecondary}
                meta={item.meta}
                onToggle={item.onToggle}
              />
            ))}
          </div>
        )}

        {sceneCatalogStatus === 'fallback' && (
          <p className="inline-notice inline-notice--warning">
            素材接口暂不可用，当前显示本地清单；启动 FastAPI 后即可执行完整分析。
            {sceneCatalogError ? ` ${sceneCatalogError}` : ''}
          </p>
        )}

        <label className="spatial-prompt-field">
          <span>Aholo AI 空间改造提示</span>
          <textarea value={spatialPrompt} onChange={(event) => setSpatialPrompt(event.target.value)} rows={2} />
        </label>

        {analysisError && <p className="inline-notice inline-notice--error" role="alert">{analysisError}</p>}
        <div className="page-actions page-actions--split">
          <Button variant="secondary" onClick={() => navigate(ImplementationRoutes.c01)}>返回上一步</Button>
          <Button disabled={!selectedTotal || isAnalyzing} onClick={handleAnalyze}>
            {isAnalyzing ? <><LoaderCircle className="spin" size={18} />Agent 分析中…</> : '开始全链路分析'}
          </Button>
        </div>
      </section>
      <aside className="creation-aside">
        <GuidancePanel title="采集建议">
          <GuidanceItem icon={Link2} title="先启动本机 Bridge">
            采集前请运行 capture_bridge（demo_auto），并保证相机 USB 为安卓模式。
          </GuidanceItem>
          <GuidanceItem icon={Image} title="覆盖主要空间与构件区域">尽量采集项目中具有代表性的空间与关键构件区域。</GuidanceItem>
          <GuidanceItem icon={Focus} title="保证关键构件有清晰视角">对需要评估的建筑构件尽量保留清晰、完整的视角。</GuidanceItem>
          <GuidanceItem icon={Box} title="确认后再入库">预览满意并填写空间名称后点「确认」，卡片会出现在下方列表。</GuidanceItem>
          <GuidanceItem icon={FileText} title="分析仍可选样例">本期全链路分析仍使用样例场景 ID；实拍用于展示与后续对接。</GuidanceItem>
        </GuidancePanel>
        <section className="panel guidance-panel mini-tip-panel">
          <span className="guidance-icon guidance-icon--accent"><Lightbulb size={25} /></span>
          <div><h2>小提示</h2><p>点击「采集现场照片」开始；确认后可继续采集下一空间，或选择样例开始分析。</p></div>
        </section>
      </aside>
    </div>
  )
}

function SceneCard({
  index,
  name,
  thumbnailUrl,
  selected,
  badgePrimary,
  badgeSecondary,
  meta,
  onToggle,
}: {
  index: number
  name: string
  thumbnailUrl: string
  selected: boolean
  badgePrimary: string
  badgeSecondary: string
  meta: string
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      className={`scene-card scene-card--selectable ${selected ? 'is-selected' : ''}`}
      aria-pressed={selected}
      aria-label={`${selected ? '取消选择' : '选择'} ${name}`}
      onClick={onToggle}
    >
      <span className="scene-card__media">
        <img src={thumbnailUrl} alt={`${name} 360° 全景`} loading="lazy" />
        <span className="scene-card__check"><Check size={15} /></span>
      </span>
      <span className="scene-card__content">
        <span className="scene-card__name"><strong>场景 {String(index).padStart(2, '0')}　{name}</strong></span>
        <span className="scene-card__badges"><em>{badgePrimary}</em><em>{badgeSecondary}</em></span>
        <small>{meta}</small>
      </span>
    </button>
  )
}
