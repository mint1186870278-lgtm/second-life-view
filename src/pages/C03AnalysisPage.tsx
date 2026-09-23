import { Box, Check, Crosshair, FileText, Image, Lightbulb, Link2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { buildCreationAnalysisSummary } from '../selectors'
import { Button, CreationShell, GuidanceItem, GuidancePanel, MediaFallback } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

export function C03AnalysisPage() {
  return (
    <CreationShell activeStep={3}>
      <ProjectSessionGate><C03AnalysisContent /></ProjectSessionGate>
    </CreationShell>
  )
}

function C03AnalysisContent() {
  const navigate = useNavigate()
  const { project, scenes, componentInstances, assessmentBatches, verificationItems } = useProjectSession()
  if (!project) return null
  const summary = buildCreationAnalysisSummary(project.project_id, scenes, componentInstances, assessmentBatches, verificationItems)

  return (
    <div className="creation-layout">
      <section className="panel creation-main-panel analysis-main">
        <h1 className="page-title">分析处理完成</h1>
        <p className="page-description">系统已完成已接入现场素材的处理、构件识别与初步评估，可进入再生视图继续核对。</p>
        <section className="analysis-hero">
          <div className="progress-ring"><strong>100%</strong></div>
          <div>
            <h2>分析处理已完成</h2>
            <p>{summary.sceneCount} 个场景 · {summary.componentCount} 个构件 · {summary.assessmentBatchCount} 个分组</p>
            <span>所有任务已成功完成，可进入再生视图。</span>
          </div>
        </section>
        <div className="analysis-stages">
          <AnalysisStage icon={Image} title="素材预处理">{summary.processedScenes.length} 个已接入场景已完成预处理，包括图像增强、格式标准化与空间信息提取。</AnalysisStage>
          <AnalysisStage icon={Box} title="构件识别与分组">识别 {summary.componentCount} 个构件，形成 {summary.assessmentBatchCount} 组，已按构件类型进行初步分组。</AnalysisStage>
          <AnalysisStage icon={Crosshair} title="初步评估草案">生成路径建议与待核实事项，为后续评估提供依据。</AnalysisStage>
        </div>
        <div className="metrics-grid">
          <MetricCard icon={FileText} label="已识别构件" value={summary.componentCount} unit="个" />
          <MetricCard icon={Crosshair} label="待核实事项" value={summary.activeVerificationItemCount} unit="项" accent />
          <MetricCard icon={FileText} label="评估草案" value={1} unit="份" />
        </div>
        <div className="section-heading section-heading--compact">
          <h2>已处理场景</h2><span>{summary.processedScenes.length} / {summary.sceneCount}</span>
        </div>
        <div className="processed-scenes">
          {summary.processedScenes.map((scene, index) => (
            <article className="processed-scene" key={scene.scene_id}>
              <MediaFallback label={`${scene.name} 媒体占位`} />
              <strong>场景 {String(index + 1).padStart(2, '0')}　{scene.name}</strong>
              <span><Check size={14} /> 已完成</span>
            </article>
          ))}
        </div>
        <div className="page-actions page-actions--split">
          <Button variant="secondary" onClick={() => navigate(ImplementationRoutes.c02)}>返回上一步</Button>
          <Button onClick={() => navigate(ImplementationRoutes.w01)}>进入再生视图</Button>
        </div>
      </section>
      <aside className="creation-aside">
        <GuidancePanel title="本次处理结果">
          <GuidanceItem icon={Box} title="形成构件与分组">基于本次现场采集素材，自动识别构件并按类型进行分组。</GuidanceItem>
          <GuidanceItem icon={Crosshair} title="标记待核实事项">识别过程中发现的关键问题已标记，便于后续确认。</GuidanceItem>
          <GuidanceItem icon={FileText} title="生成初步路径建议">基于构件识别结果，生成初步的再生路径建议与资源循环方案。</GuidanceItem>
          <GuidanceItem icon={Link2} title="可进入再生视图继续核对">现在你可以进入再生视图，继续核对构件、补充证据并完善评估草案。</GuidanceItem>
        </GuidancePanel>
        <section className="panel guidance-panel mini-tip-panel">
          <span className="guidance-icon guidance-icon--accent"><Lightbulb size={25} /></span>
          <div><h2>小提示</h2><p>进入再生视图后，你可以继续核对构件、补充证据、调整建议路径并生成评估草案。</p></div>
        </section>
      </aside>
    </div>
  )
}

function AnalysisStage({ icon: Icon, title, children }: { icon: typeof Image; title: string; children: ReactNode }) {
  return (
    <div className="analysis-stage">
      <div className="analysis-stage__name"><Icon size={22} />{title}</div>
      <span className="analysis-stage__divider" />
      <div className="analysis-stage__result"><strong><Check size={15} />已完成</strong><span>{children}</span></div>
      <span className="analysis-stage__arrow">›</span>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, unit, accent = false }: { icon: typeof Image; label: string; value: number; unit: string; accent?: boolean }) {
  return (
    <div className="metric-card">
      <span className={`metric-card__icon ${accent ? 'is-accent' : ''}`}><Icon size={22} /></span>
      <div><span>{label}</span><strong>{value}<small>{unit}</small></strong></div>
    </div>
  )
}
