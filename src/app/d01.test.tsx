// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import type { HumanVerificationService } from '../application'
import { FixtureProjectDataRepository } from '../data'
import { creationDemoGraph, CREATION_DEMO_PROJECT_ID } from '../fixtures'
import type { D01NavigationContext } from '../navigation'
import { D01BatchDetailPage } from '../pages'
import { App } from './App'
import { ProjectSessionProvider } from './ProjectSessionContext'

afterEach(cleanup)

const route = '/workspace/batches/fixture-batch-wood'

const viewContext: D01NavigationContext = {
  source: 'view',
  batch_id: 'fixture-batch-wood',
  focus_target: 'fixing_method',
  return_state: {
    scene_id: 'fixture-scene-roof',
    viewer_mode: 'site',
    zoom_level: 1.3,
  },
}

const verificationContext: D01NavigationContext = {
  source: 'review-verification',
  source_tab: 'review-verification',
  batch_id: 'fixture-batch-wood',
  focus_target: 'hidden_damage',
  return_state: {
    source_tab: 'review-verification',
    material_filter: '木材',
    scene_filter: 'all',
    verification_type_filter: 'all',
    verification_status_filter: 'active',
    search: '',
    expanded_material: '木材',
  },
}

function NavigationProbe() {
  const location = useLocation()
  return <output hidden aria-label="current-route">{location.pathname}</output>
}

function renderD01(context: D01NavigationContext = viewContext) {
  return render(<MemoryRouter initialEntries={[{ pathname: route, state: context }]}><App /><NavigationProbe /></MemoryRouter>)
}

function renderD01WithService(service: HumanVerificationService) {
  const repository = new FixtureProjectDataRepository(creationDemoGraph)
  return render(<MemoryRouter initialEntries={[{ pathname: route, state: viewContext }]}>
    <ProjectSessionProvider
      projectId={CREATION_DEMO_PROJECT_ID}
      repository={repository}
      mutations={{ renameScene: async (command) => ({ scene_id: command.scene_id, name: command.name }) }}
    >
      <Routes><Route path="/workspace/batches/:batchId" element={<D01BatchDetailPage verificationService={service} />} /></Routes>
    </ProjectSessionProvider>
  </MemoryRouter>)
}

describe('D01 AssessmentBatch detail and human verification', () => {
  it('renders the canonical Batch hierarchy and only the three confirmed verification fields', async () => {
    const view = renderD01()
    expect(await screen.findByRole('heading', { name: '木质固定柜体' })).toBeTruthy()
    expect(screen.getByLabelText('评估分组摘要')).toBeTruthy()
    expect(view.container.querySelectorAll('.d01-verification-field')).toHaveLength(3)
    expect(screen.getAllByText('固定方式').length).toBeGreaterThan(0)
    expect(screen.getAllByText('隐藏腐朽').length).toBeGreaterThan(0)
    expect(screen.getAllByText('表面处理').length).toBeGreaterThan(0)
    expect(view.container.querySelectorAll('.d01-instance-chip')).toHaveLength(2)
  })

  it('edits and saves one ComponentInstance without applying the values to its sibling', async () => {
    const user = userEvent.setup()
    renderD01()
    await screen.findByRole('heading', { name: '木质固定柜体' })
    await user.click(screen.getByRole('button', { name: '可拆卸螺丝/螺栓' }))
    await user.click(screen.getByRole('button', { name: '未发现' }))
    await user.click(screen.getByRole('button', { name: '已确认有' }))
    const save = screen.getByRole('button', { name: '保存当前实例' })
    expect((save as HTMLButtonElement).disabled).toBe(false)
    await user.click(save)
    expect(await screen.findByText('当前实例核实结果已保存。')).toBeTruthy()
    expect(screen.getByRole('button', { name: /01已核实/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: /02未核实/ })).toBeTruthy()
  })

  it('protects an unsaved draft with an in-product discard dialog when switching instances', async () => {
    const user = userEvent.setup()
    renderD01()
    await screen.findByRole('heading', { name: '木质固定柜体' })
    await user.click(screen.getByRole('button', { name: '钉固' }))
    await user.click(screen.getByRole('button', { name: /02未核实/ }))
    expect(screen.getByRole('dialog', { name: '放弃未保存的修改？' })).toBeTruthy()
    await user.click(screen.getByRole('button', { name: '继续编辑' }))
    expect(screen.getByText('木质固定柜体 · 实例 01')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: /02未核实/ }))
    await user.click(screen.getByRole('button', { name: '放弃并继续' }))
    expect(screen.getByText('木质固定柜体 · 实例 02')).toBeTruthy()
  })

  it('keeps a failed save dirty and presents the application-service error', async () => {
    const user = userEvent.setup()
    const submitDraft = vi.fn().mockRejectedValue(new Error('核实结果暂时无法保存'))
    renderD01WithService({ submitDraft })
    await screen.findByRole('heading', { name: '木质固定柜体' })
    await user.click(screen.getByRole('button', { name: '钉固' }))
    await user.click(screen.getByRole('button', { name: '保存当前实例' }))
    expect(await screen.findByText('核实结果暂时无法保存')).toBeTruthy()
    expect(submitDraft).toHaveBeenCalledOnce()
    expect((screen.getByRole('button', { name: '保存当前实例' }) as HTMLButtonElement).disabled).toBe(false)
  })

  it('keeps approved upload and deferred child affordances functional', async () => {
    const user = userEvent.setup()
    renderD01()
    await screen.findByRole('heading', { name: '木质固定柜体' })
    await user.upload(screen.getByLabelText('选择现场补充照片'), new File(['photo'], 'evidence.png', { type: 'image/png' }))
    expect(await screen.findByText('已添加 1 张现场补充照片')).toBeTruthy()
    expect(screen.getByText('共 7 张')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: /查看全部6条路径/ }))
    expect(await screen.findByText(/Pathway Detail/)).toBeTruthy()
    await user.click(screen.getByRole('button', { name: '打开 360° 现场' }))
    expect(await screen.findByText(/360 Evidence Viewer/)).toBeTruthy()
  })

  it('returns to the exact source view and restores W01/W02 mode state', async () => {
    const user = userEvent.setup()
    const first = renderD01()
    await user.click(await screen.findByRole('button', { name: '返回再生视图' }))
    expect((await screen.findByRole('button', { name: '现场视图' })).getAttribute('aria-pressed')).toBe('true')
    first.unmount()

    renderD01(verificationContext)
    await user.click(await screen.findByRole('button', { name: '返回项目审查' }))
    await waitFor(() => expect(screen.getByRole('tab', { name: '待核实' }).getAttribute('aria-selected')).toBe('true'))
  })

  it('opens the approved project context menu and keeps New Project navigation functional', async () => {
    const user = userEvent.setup()
    renderD01()
    await user.click(await screen.findByRole('button', { name: /HSBC MKK · 屋顶花园/ }))
    await user.click(screen.getByRole('button', { name: /新建再生评估项目/ }))
    expect(screen.getByLabelText('current-route').textContent).toBe('/create/project')
  })
})
