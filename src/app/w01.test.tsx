// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { App } from './App'
import { ImplementationRoutes } from './routes'

afterEach(cleanup)

function NavigationProbe() {
  const location = useLocation()
  return (
    <div hidden>
      <output aria-label="current-route">{location.pathname}</output>
      <output aria-label="navigation-state">{JSON.stringify(location.state)}</output>
    </div>
  )
}

function renderW01() {
  return render(
    <MemoryRouter initialEntries={[ImplementationRoutes.w01]}>
      <App />
      <NavigationProbe />
    </MemoryRouter>,
  )
}

describe('W01 Regeneration View', () => {
  it('consumes canonical ProjectSession data without a Creation provider', async () => {
    renderW01()
    expect(await screen.findByRole('heading', { name: '再生视图' })).toBeTruthy()
    expect(screen.getByText('HSBC MKK · 屋顶花园')).toBeTruthy()
    expect(screen.getByText('41')).toBeTruthy()
  })

  it('selects the first canonical Scene by default and switches by scene_id', async () => {
    const user = userEvent.setup()
    renderW01()
    const roof = await screen.findByRole('button', { name: /场景 01屋顶花园/ })
    expect(roof.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('img', { name: '屋顶花园 360° 场景视觉占位' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '查看 木质围栏 详情' })).toBeTruthy()

    await user.click(screen.getByRole('button', { name: /场景 02休息区/ }))
    expect(screen.getByRole('img', { name: '休息区 360° 场景视觉占位' })).toBeTruthy()
    expect(screen.getByRole('button', { name: '查看 木质围栏 详情' })).toBeTruthy()
  })

  it('hides and restores regeneration-only overlays when switching viewer mode', async () => {
    const user = userEvent.setup()
    renderW01()
    await screen.findByRole('button', { name: '查看 木质围栏 详情' })
    expect(screen.getByLabelText('再生潜力')).toBeTruthy()

    await user.click(screen.getByRole('button', { name: '现场视图' }))
    expect(screen.queryByRole('button', { name: '查看 木质围栏 详情' })).toBeNull()
    expect(screen.queryByLabelText('再生潜力')).toBeNull()
    expect(screen.queryByRole('heading', { name: '待处理事项' })).toBeNull()

    await user.click(screen.getByRole('button', { name: '再生视图', pressed: false }))
    expect(screen.getByRole('button', { name: '查看 木质围栏 详情' })).toBeTruthy()
  })

  it('keeps zoom as isolated viewer presentation state and resets it on Scene switch', async () => {
    const user = userEvent.setup()
    renderW01()
    await screen.findByRole('heading', { name: '再生视图' })
    expect(screen.getByLabelText('当前缩放').textContent).toBe('100%')
    await user.click(screen.getByRole('button', { name: '放大' }))
    expect(screen.getByLabelText('当前缩放').textContent).toBe('115%')
    await user.click(screen.getByRole('button', { name: /场景 02休息区/ }))
    expect(screen.getByLabelText('当前缩放').textContent).toBe('100%')
  })

  it('navigates from a hotspot with canonical batch_id and source=view context', async () => {
    const user = userEvent.setup()
    renderW01()
    await user.click(await screen.findByRole('button', { name: '查看 木质围栏 详情' }))

    expect(screen.getByLabelText('current-route').textContent).toBe('/workspace/batches/fixture-batch-wood')
    const state = screen.getByLabelText('navigation-state').textContent ?? ''
    expect(state).toContain('"source":"view"')
    expect(state).toContain('"scene_id":"fixture-scene-roof"')
    expect(state).toContain('"viewer_mode":"regeneration"')
  })

  it('carries the confirmed task focus_target into D01 context', async () => {
    const user = userEvent.setup()
    renderW01()
    await user.click(await screen.findByRole('button', { name: '确认固定方式' }))

    expect(document.getElementById('d01-field-fixing_method')).toBeTruthy()
    expect(screen.getByLabelText('navigation-state').textContent).toContain('"focus_target":"fixing_method"')
  })

  it('enters the single W02 route from the Project Review action', async () => {
    const user = userEvent.setup()
    renderW01()
    await user.click(await screen.findByRole('button', { name: /进入项目审查/ }))
    expect(screen.getByLabelText('current-route').textContent).toBe(ImplementationRoutes.w02)
  })

  it('keeps Regeneration Potential informational and non-clickable', async () => {
    renderW01()
    const card = await screen.findByLabelText('再生潜力')
    expect(card.tagName).toBe('SECTION')
    expect(card.querySelector('button')).toBeNull()
    expect(card.textContent).toContain('30 件构件，值得在拆除前再看一眼。')
  })

  it('uses the shared Workspace header and isolates component-group overflow', async () => {
    const view = renderW01()
    await waitFor(() => expect(view.container.querySelector('.workspace-header')).not.toBeNull())

    expect(view.container.querySelectorAll('.workspace-header')).toHaveLength(1)
    const groupList = view.container.querySelector('[data-scroll-region=component-groups]')
    expect(groupList).not.toBeNull()
    expect(groupList?.parentElement?.classList.contains('w01-sidebar-supplement')).toBe(true)
  })

  it('matches the approved W01 CTA and right-stack content', async () => {
    renderW01()
    const review = await screen.findByRole('button', { name: '进入项目审查' })
    expect(review.querySelector('svg')).toBeNull()

    const taskCard = screen.getByRole('heading', { name: '待处理事项' }).closest('section')
    expect(taskCard).not.toBeNull()
    const rows = taskCard!.querySelectorAll('.w01-task-row')
    expect(rows).toHaveLength(4)
    expect(Array.from(rows).map((row) => row.textContent)).toEqual([
      '确认固定方式', '确认表面涂层', '检查隐藏损伤', '核实候选渠道',
    ])

    expect(screen.getByText('当前结果基于现场素材自动识别与初步判断生成。关键构件状态、证据不足或与建议路径需由人工进一步核实。')).toBeTruthy()
    expect(screen.queryByText('演示结构 · 非正式映射')).toBeNull()
    expect(screen.queryByText('演示投影')).toBeNull()
    expect(screen.queryByText('非权威演示投影')).toBeNull()
  })
})
