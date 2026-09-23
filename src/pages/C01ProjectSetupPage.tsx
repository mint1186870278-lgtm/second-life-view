import { Building2, Box, FileText, Lightbulb, MapPin } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCreationFlow } from '../app/CreationFlowContext'
import { ImplementationRoutes } from '../app/routes'
import { demoProjectOptionSource } from '../config'
import {
  Button,
  CreationShell,
  FormField,
  GuidanceItem,
  GuidancePanel,
  Input,
  Select,
  Textarea,
} from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

type FieldErrors = Partial<Record<'name' | 'region' | 'projectType' | 'projectStage', string>>

export function C01ProjectSetupPage() {
  return (
    <CreationShell activeStep={1}>
      <ProjectSessionGate><C01ProjectSetupContent /></ProjectSessionGate>
    </CreationShell>
  )
}

function C01ProjectSetupContent() {
  const navigate = useNavigate()
  const { projectDraft, updateProjectDraft } = useCreationFlow()
  const [errors, setErrors] = useState<FieldErrors>({})

  function submit(event: FormEvent) {
    event.preventDefault()
    const nextErrors: FieldErrors = {}
    if (!projectDraft.name.trim()) nextErrors.name = '请输入项目名称'
    if (!projectDraft.region) nextErrors.region = '请选择所在地区'
    if (!projectDraft.projectType) nextErrors.projectType = '请选择项目类型'
    if (!projectDraft.projectStage) nextErrors.projectStage = '请选择项目阶段'
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) navigate(ImplementationRoutes.c02)
  }

  return (
    <div className="creation-layout">
      <section className="panel creation-main-panel">
        <h1 className="page-title">新建再生评估项目</h1>
        <p className="page-description">填写项目基本信息，随后接入现场 360° 素材并进入构件识别与再生评估流程。</p>
        <form onSubmit={submit} noValidate>
          <FormField id="project-name" label="项目名称" required error={errors.name}>
            <Input
              id="project-name"
              value={projectDraft.name}
              maxLength={100}
              aria-invalid={Boolean(errors.name)}
              onChange={(event) => updateProjectDraft({ name: event.target.value })}
            />
            <div className="character-count">{projectDraft.name.length} / 100</div>
          </FormField>
          <FormField id="project-region" label="所在地区" required error={errors.region}>
            <Select
              id="project-region"
              value={projectDraft.region}
              options={demoProjectOptionSource.regionOptions}
              icon={<MapPin size={27} />}
              aria-invalid={Boolean(errors.region)}
              onChange={(event) => updateProjectDraft({ region: event.target.value })}
            />
          </FormField>
          <FormField id="project-type" label="项目类型" required error={errors.projectType}>
            <Select
              id="project-type"
              value={projectDraft.projectType}
              options={demoProjectOptionSource.projectTypeOptions}
              icon={<Box size={27} />}
              aria-invalid={Boolean(errors.projectType)}
              onChange={(event) => updateProjectDraft({ projectType: event.target.value })}
            />
          </FormField>
          <FormField id="project-stage" label="项目阶段" required error={errors.projectStage}>
            <Select
              id="project-stage"
              value={projectDraft.projectStage}
              options={demoProjectOptionSource.projectStageOptions}
              icon={<Building2 size={27} />}
              aria-invalid={Boolean(errors.projectStage)}
              onChange={(event) => updateProjectDraft({ projectStage: event.target.value })}
            />
          </FormField>
          <FormField id="project-description" label="项目说明（选填）">
            <Textarea
              id="project-description"
              value={projectDraft.description}
              maxLength={500}
              onChange={(event) => updateProjectDraft({ description: event.target.value })}
            />
            <div className="character-count">{projectDraft.description.length} / 500</div>
          </FormField>
          <div className="form-actions">
            <Button variant="secondary" type="button">取消</Button>
            <Button type="submit">下一步：素材接入</Button>
          </div>
        </form>
      </section>
      <aside className="creation-aside">
        <GuidancePanel title="项目创建提示">
          <GuidanceItem icon={FileText} title="项目名称" accent>建议使用建筑名 + 区域或部位命名，便于后续素材与评估草案关联。</GuidanceItem>
          <GuidanceItem icon={MapPin} title="所在地区">将影响后续本地可行方案、政策依据与参考案例匹配。</GuidanceItem>
          <GuidanceItem icon={Box} title="项目类型">用于建立本次评估所处的改造、翻新或拆除语境。</GuidanceItem>
          <GuidanceItem icon={Building2} title="项目阶段">会影响现场可观察证据范围，以及后续人工补证重点。</GuidanceItem>
          <GuidanceItem icon={FileText} title="项目说明">可补充本次评估目标、构件关注重点或现场特殊条件。</GuidanceItem>
        </GuidancePanel>
        <section className="panel guidance-panel mini-tip-panel">
          <span className="guidance-icon guidance-icon--accent"><Lightbulb size={25} /></span>
          <div><h2>小提示</h2><p>项目创建后，可随时通过工作区顶部的项目切换器进入其他项目或新建评估项目。</p></div>
        </section>
      </aside>
    </div>
  )
}
