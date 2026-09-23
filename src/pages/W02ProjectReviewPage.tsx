import {
  ChevronDown,
  ChevronRight,
  Image as ImageIcon,
  Leaf,
  LoaderCircle,
  Search,
  Sparkles,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchDemoReviewGroups,
  generateDemoComponentPreview,
  requestDemoComponentDesignAdvice,
  type DemoComponentDesignAdvice,
  type DemoComponentPreview,
  type DemoGroup,
} from '../api/demo'
import { useCreationFlow } from '../app/CreationFlowContext'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ImplementationRoutes } from '../app/routes'
import { getWorkspaceDestinationRoute, WORKSPACE_NAVIGATION_ITEMS } from '../app/workspaceNavigation'
import { Button, WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

type ReviewTab = 'review' | 'verification'

interface ReviewFilters {
  material: string
  scene: string
  evidence: string
  search: string
}

interface MaterialSection {
  material: string
  groups: DemoGroup[]
}

const EMPTY_FILTERS: ReviewFilters = {
  material: 'all',
  scene: 'all',
  evidence: 'all',
  search: '',
}

const CATEGORY_LABELS: Record<string, string> = {
  cabinet: '柜体',
  chair: '座椅',
  door: '门',
  sofa: '沙发',
  table: '桌台',
  window: '窗',
}

const EVIDENCE_LABELS: Record<string, string> = {
  supported: '有依据',
  conditional: '待核实',
  insufficient_evidence: '证据不足',
  not_applicable: '不适用',
}

const PATHWAY_LABELS: Record<string, string> = {
  KEEP_IN_PLACE: '原位保留',
  DIRECT_REUSE: '直接再利用',
  REFURBISH: '修复翻新',
  REPURPOSE: '改造再利用',
  MATERIAL_RECOVERY: '材料回收',
  DISPOSAL: '处置',
}

export function W02ProjectReviewPage() {
  return <ProjectSessionGate><W02ProjectReviewContent /></ProjectSessionGate>
}

function W02ProjectReviewContent() {
  const navigate = useNavigate()
  const { project } = useProjectSession()
  const { analysisResult, projectDraft } = useCreationFlow()
  const [tab, setTab] = useState<ReviewTab>('review')
  const [filters, setFilters] = useState<ReviewFilters>(EMPTY_FILTERS)
  const [groups, setGroups] = useState<DemoGroup[]>(analysisResult?.groups ?? [])
  const [loading, setLoading] = useState(!analysisResult?.groups.length)
  const [loadError, setLoadError] = useState<string>()
  const [expandedMaterial, setExpandedMaterial] = useState<string | null>(null)
  const [previewGroup, setPreviewGroup] = useState<DemoGroup | null>(null)
  const [advice, setAdvice] = useState<DemoComponentDesignAdvice | null>(null)
  const [preview, setPreview] = useState<DemoComponentPreview | null>(null)
  const [previewError, setPreviewError] = useState<string>()
  const [adviceLoading, setAdviceLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const region = projectDraft.region || project?.region || undefined

  useEffect(() => {
    let active = true
    if (analysisResult?.groups.length) {
      setGroups(analysisResult.groups)
      setLoading(false)
      setLoadError(undefined)
      return () => { active = false }
    }
    setLoading(true)
    fetchDemoReviewGroups()
      .then((nextGroups) => {
        if (!active) return
        setGroups(nextGroups)
        setLoadError(undefined)
      })
      .catch((error: unknown) => {
        if (!active) return
        setLoadError(error instanceof Error ? error.message : '无法读取 YOLO 构件分组')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [analysisResult])

  const materialOptions = useMemo(() => uniqueOptions(groups.map((group) => group.material || '材质待核实')), [groups])
  const sceneOptions = useMemo(() => uniqueOptions(groups.map((group) => group.scene_name)), [groups])
  const filteredGroups = useMemo(() => groups.filter((group) => matchesFilters(group, filters)), [filters, groups])
  const reviewSections = useMemo(() => groupByMaterial(filteredGroups), [filteredGroups])
  const verificationSections = useMemo(
    () => groupByMaterial(filteredGroups.filter((group) => group.evidence_status !== 'supported')),
    [filteredGroups],
  )
  const activeSections = tab === 'review' ? reviewSections : verificationSections
  const eligiblePreviewCount = useMemo(
    () => groups.filter(canGeneratePreview).length,
    [groups],
  )

  useEffect(() => {
    if (!activeSections.length) {
      setExpandedMaterial(null)
      return
    }
    setExpandedMaterial((current) => (
      current && activeSections.some((section) => section.material === current)
        ? current
        : activeSections[0].material
    ))
  }, [activeSections])

  async function openPreview(target: DemoGroup) {
    setPreviewGroup(target)
    setAdvice(null)
    setPreview(null)
    setPreviewError(undefined)
    setAdviceLoading(true)
    try {
      setAdvice(await requestDemoComponentDesignAdvice(target.id, region))
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : '无法生成改造建议')
    } finally {
      setAdviceLoading(false)
    }
  }

  async function generatePreview() {
    if (!previewGroup || !advice) return
    setPreviewLoading(true)
    setPreviewError(undefined)
    try {
      setPreview(await generateDemoComponentPreview(previewGroup.id, advice, region))
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : '无法生成再生预览图')
    } finally {
      setPreviewLoading(false)
    }
  }

  function openDetail(groupId: string) {
    navigate(ImplementationRoutes.d01.replace(':batchId', encodeURIComponent(groupId)))
  }

  return (
    <>
      <WorkspaceShell
        projectName={projectDraft.name || project?.name || '当前项目'}
        projectContextLabel={region}
        items={WORKSPACE_NAVIGATION_ITEMS}
        activeDestination="review"
        onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
        headerCenter={<div className="w02-header-title">项目审查</div>}
        headerAction={<Button className="w02-view-entry" onClick={() => navigate(ImplementationRoutes.w01)}>返回再生视图</Button>}
        contentClassName="w02-main"
      >
        <section className="w02-page-head">
          <div>
            <p className="w02-eyebrow">YOLO 构件审查</p>
            <h1>项目审查</h1>
            <p>按材质汇总实际识别到的构件子图；所有分组已完成初审，待核实项可进入详情补充证据。</p>
          </div>
          <div className="w02-page-metrics" aria-label="审查统计">
            <span><strong>{groups.length}</strong> 构件分组</span>
            <span><strong>{eligiblePreviewCount}</strong> 可再生预览</span>
          </div>
        </section>

        <div className="w02-tabs" role="tablist" aria-label="项目审查视图">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'review'}
            className={tab === 'review' ? 'is-active' : ''}
            onClick={() => setTab('review')}
          >
            全部构件
            <span>{filteredGroups.length}</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'verification'}
            className={tab === 'verification' ? 'is-active' : ''}
            onClick={() => setTab('verification')}
          >
            待核实
            <span>{filteredGroups.filter((group) => group.evidence_status !== 'supported').length}</span>
          </button>
        </div>

        <ReviewToolbar
          filters={filters}
          materials={materialOptions}
          scenes={sceneOptions}
          onChange={setFilters}
        />

        {loading && <div className="w02-state"><LoaderCircle className="spin" />正在读取构件识别结果…</div>}
        {!loading && loadError && <div className="w02-state is-error">{loadError}</div>}
        {!loading && !loadError && !activeSections.length && (
          <div className="w02-state">没有符合当前筛选条件的构件分组。</div>
        )}
        {!loading && !loadError && activeSections.map((section) => {
          const expanded = expandedMaterial === section.material
          return (
            <section className="w02-material-section" key={section.material}>
              <button
                className="w02-material-header"
                type="button"
                aria-expanded={expanded}
                onClick={() => setExpandedMaterial(expanded ? null : section.material)}
              >
                <span className={`w02-material-swatch ${materialTone(section.material)}`} />
                <span><strong>{section.material}</strong><small>{section.groups.length} 个 YOLO 构件分组</small></span>
                {expanded ? <ChevronDown /> : <ChevronRight />}
              </button>
              {expanded && (
                <div className="w02-component-grid">
                  {section.groups.map((group) => (
                    <ComponentCard
                      group={group}
                      key={group.id}
                      onPreview={() => void openPreview(group)}
                      onOpenDetail={() => openDetail(group.id)}
                    />
                  ))}
                </div>
              )}
            </section>
          )
        })}
      </WorkspaceShell>
      {previewGroup && (
        <RegenerationPreviewDialog
          group={previewGroup}
          advice={advice}
          preview={preview}
          error={previewError}
          adviceLoading={adviceLoading}
          previewLoading={previewLoading}
          onClose={() => setPreviewGroup(null)}
          onGenerate={() => void generatePreview()}
        />
      )}
    </>
  )
}

function ReviewToolbar({
  filters,
  materials,
  scenes,
  onChange,
}: {
  filters: ReviewFilters
  materials: readonly string[]
  scenes: readonly string[]
  onChange: (next: ReviewFilters) => void
}) {
  return (
    <section className="w02-toolbar" aria-label="构件筛选">
      <label>
        <span>材质</span>
        <select value={filters.material} onChange={(event) => onChange({ ...filters, material: event.target.value })}>
          <option value="all">全部材质</option>
          {materials.map((material) => <option key={material} value={material}>{material}</option>)}
        </select>
      </label>
      <label>
        <span>场景</span>
        <select value={filters.scene} onChange={(event) => onChange({ ...filters, scene: event.target.value })}>
          <option value="all">全部场景</option>
          {scenes.map((scene) => <option key={scene} value={scene}>{scene}</option>)}
        </select>
      </label>
      <label>
        <span>证据</span>
        <select value={filters.evidence} onChange={(event) => onChange({ ...filters, evidence: event.target.value })}>
          <option value="all">全部证据状态</option>
          <option value="supported">有依据</option>
          <option value="conditional">待核实</option>
          <option value="insufficient_evidence">证据不足</option>
        </select>
      </label>
      <label className="w02-search">
        <Search size={17} />
        <input
          value={filters.search}
          placeholder="搜索构件、材质或场景"
          aria-label="搜索构件、材质或场景"
          onChange={(event) => onChange({ ...filters, search: event.target.value })}
        />
      </label>
    </section>
  )
}

function ComponentCard({
  group,
  onPreview,
  onOpenDetail,
}: {
  group: DemoGroup
  onPreview: () => void
  onOpenDetail: () => void
}) {
  const eligible = canGeneratePreview(group)
  const evidence = group.evidence_status || 'conditional'
  const pathway = group.recommended_pathway || 'DIRECT_REUSE'
  return (
    <article className="w02-component-card">
      <button className="w02-component-image" type="button" onClick={onOpenDetail} aria-label={`查看 ${group.group_name || group.label} 详情`}>
        {group.crop_url ? <img src={group.crop_url} alt={`${group.group_name || group.label} 的 YOLO 构件裁切图`} loading="lazy" /> : <ImageIcon />}
      </button>
      <div className="w02-component-copy">
        <div className="w02-component-title-row">
          <h2>{group.group_name || categoryLabel(group)}</h2>
          <span className={`w02-evidence-pill ${evidence}`}>{EVIDENCE_LABELS[evidence] || '待核实'}</span>
        </div>
        <p>{group.scene_name} · {group.material || '材质待核实'}</p>
        <div className="w02-component-tags">
          <span>{PATHWAY_LABELS[pathway] || pathway}</span>
          <span>{group.detected_count} 个相似实例</span>
        </div>
      </div>
      <div className="w02-component-actions">
        {eligible ? (
          <button className="w02-preview-action" type="button" onClick={onPreview}><Sparkles size={15} />再生预览图</button>
        ) : (
          <button className="w02-detail-action" type="button" onClick={onOpenDetail}>
            {evidence === 'supported' ? '查看详情' : '去核实'}<ChevronRight size={15} />
          </button>
        )}
      </div>
    </article>
  )
}

function RegenerationPreviewDialog({
  group,
  advice,
  preview,
  error,
  adviceLoading,
  previewLoading,
  onClose,
  onGenerate,
}: {
  group: DemoGroup
  advice: DemoComponentDesignAdvice | null
  preview: DemoComponentPreview | null
  error?: string
  adviceLoading: boolean
  previewLoading: boolean
  onClose: () => void
  onGenerate: () => void
}) {
  return (
    <div className="w02-modal-backdrop" role="presentation">
      <section className="w02-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="w02-preview-title">
        <button className="w02-modal-close" type="button" aria-label="关闭再生预览" onClick={onClose}><X /></button>
        <div className="w02-preview-dialog__head">
          <span><Sparkles size={18} />Design Agent</span>
          <h2 id="w02-preview-title">{group.group_name || categoryLabel(group)} · 再生预览图</h2>
          <p>先确认文字版改造建议；确认后才会调用 `qwen-image-3.0-pro` 生成对象子图的翻新预览。</p>
        </div>
        <div className="w02-preview-dialog__body">
          <div className="w02-preview-source">
            {group.crop_url && <img src={group.crop_url} alt={`${group.group_name || group.label} 原始子图`} />}
            <small>YOLO 检测裁切图</small>
          </div>
          <div className="w02-advice-panel">
            {adviceLoading && <div className="w02-dialog-state"><LoaderCircle className="spin" />Design Agent 正在生成建议…</div>}
            {!adviceLoading && error && <div className="w02-dialog-state is-error">{error}</div>}
            {!adviceLoading && advice && (
              <>
                <h3>{advice.title}</h3>
                <AdviceRow label="材质" value={advice.material} />
                <AdviceRow label="颜色" value={advice.color} />
                <AdviceRow label="表面" value={advice.surface} />
                <AdviceRow label="施工" value={advice.construction} />
                <p className="w02-advice-rationale">{advice.rationale}</p>
              </>
            )}
          </div>
        </div>
        {preview && (
          <figure className="w02-generated-preview">
            <img src={preview.image_url} alt={`${group.group_name || group.label} 的翻新后再生预览`} />
            <figcaption>{preview.is_offline_fallback ? '离线演示预览：未配置百炼密钥时使用本地视觉回退。' : '已由 qwen-image-3.0-pro 生成。'}</figcaption>
          </figure>
        )}
        <div className="w02-preview-dialog__actions">
          <Button variant="secondary" onClick={onClose}>关闭</Button>
          {advice && !preview && <Button disabled={previewLoading} onClick={onGenerate}>{previewLoading ? <><LoaderCircle className="spin" size={16} />生成中…</> : <><Leaf size={16} />同意并生成预览图</>}</Button>}
        </div>
      </section>
    </div>
  )
}

function AdviceRow({ label, value }: { label: string; value: string }) {
  return <div className="w02-advice-row"><strong>{label}</strong><span>{value}</span></div>
}

function matchesFilters(group: DemoGroup, filters: ReviewFilters): boolean {
  const material = group.material || '材质待核实'
  const evidence = group.evidence_status || 'conditional'
  const searchText = [group.group_name, group.label, group.scene_name, material, categoryLabel(group)].join(' ').toLowerCase()
  return (
    (filters.material === 'all' || material === filters.material)
    && (filters.scene === 'all' || group.scene_name === filters.scene)
    && (filters.evidence === 'all' || evidence === filters.evidence)
    && (!filters.search.trim() || searchText.includes(filters.search.trim().toLowerCase()))
  )
}

function groupByMaterial(groups: readonly DemoGroup[]): MaterialSection[] {
  const materialMap = new Map<string, DemoGroup[]>()
  groups.forEach((group) => {
    const material = group.material || '材质待核实'
    const existing = materialMap.get(material) ?? []
    existing.push(group)
    materialMap.set(material, existing)
  })
  return [...materialMap.entries()]
    .sort(([left], [right]) => left.localeCompare(right, 'zh-Hans'))
    .map(([material, materialGroups]) => ({
      material,
      groups: [...materialGroups].sort((left, right) => right.confidence - left.confidence),
    }))
}

function uniqueOptions(values: readonly string[]): string[] {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right, 'zh-Hans'))
}

function categoryLabel(group: DemoGroup): string {
  return CATEGORY_LABELS[group.category] || group.label
}

function canGeneratePreview(group: DemoGroup): boolean {
  return Boolean(
    group.can_generate_preview
    || (group.evidence_status === 'supported' && ['REFURBISH', 'REPURPOSE'].includes(group.recommended_pathway || '')),
  )
}

function materialTone(material: string): string {
  if (material.includes('木')) return 'wood'
  if (material.includes('金属')) return 'metal'
  if (material.includes('织物')) return 'fabric'
  if (material.includes('玻璃')) return 'glass'
  return 'other'
}
