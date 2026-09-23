// @vitest-environment jsdom
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
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

function renderW02() {
  return render(
    <MemoryRouter initialEntries={[ImplementationRoutes.w02]}>
      <App />
      <NavigationProbe />
    </MemoryRouter>,
  )
}

describe('W02 Dual-view Project Review', () => {
  it('defaults to W02-A with exactly the four approved Summary cards', async () => {
    renderW02()
    expect(await screen.findByRole('heading', { name: '项目审查' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: '评估草案' }).getAttribute('aria-selected')).toBe('true')
    const summary = screen.getByLabelText('评估草案概览')
    expect(summary.querySelectorAll('[data-summary-card]')).toHaveLength(4)
    expect(Array.from(summary.querySelectorAll('[data-summary-card]')).map((card) => card.getAttribute('data-summary-card'))).toEqual([
      '评估分组', '已审查', '需关注', '场景',
    ])
    expect(screen.queryByText('待核实分组')).toBeNull()
  })

  it('renders canonical pending counts and filters W02-A from Summary cards', async () => {
    const user = userEvent.setup()
    renderW02()
    const woodIdentity = await screen.findByRole('button', { name: /木质固定柜体Scene01/ })
    const woodRow = woodIdentity.closest('.w02-batch-row')
    expect(woodRow).not.toBeNull()
    expect(within(woodRow as HTMLElement).getByRole('button', { name: '2项' })).toBeTruthy()

    await user.click(screen.getByRole('button', { name: /已审查1个分组/ }))
    expect(screen.queryByRole('button', { name: /木质固定柜体Scene01/ })).toBeNull()
    expect(screen.getByText('金属栏杆')).toBeTruthy()

    await user.click(screen.getByRole('button', { name: /已审查1个分组/ }))
    expect(screen.getByRole('button', { name: /木质固定柜体Scene01/ })).toBeTruthy()
  })

  it('groups W02-A rows by Material and navigates with canonical review-draft context', async () => {
    const user = userEvent.setup()
    const view = renderW02()
    await screen.findByRole('heading', { name: '项目审查' })
    const woodSection = view.container.querySelector('[data-material-section="木材"]')
    expect(woodSection).not.toBeNull()
    const pending = within(woodSection as HTMLElement).getByRole('button', { name: '2项' })
    await user.click(pending)

    expect(screen.getByLabelText('current-route').textContent).toBe('/workspace/batches/fixture-batch-wood')
    const state = screen.getByLabelText('navigation-state').textContent ?? ''
    expect(state).toContain('"source":"review-draft"')
    expect(state).toContain('"batch_id":"fixture-batch-wood"')
    expect(state).toContain('"source_tab":"review-draft"')
    expect(state).toContain('"focus_target":"human_verification"')
  })

  it('switches internally to W02-B with five cards, one global header, and no pagination', async () => {
    const user = userEvent.setup()
    const view = renderW02()
    await user.click(await screen.findByRole('tab', { name: '待核实' }))

    expect(screen.getByLabelText('current-route').textContent).toBe(ImplementationRoutes.w02)
    expect(screen.getByRole('tab', { name: '待核实' }).getAttribute('aria-selected')).toBe('true')
    expect(screen.getByLabelText('待核实概览').querySelectorAll('[data-summary-card]')).toHaveLength(5)
    expect(view.container.querySelectorAll('[data-global-verification-header]')).toHaveLength(1)
    expect(view.container.querySelectorAll('.w02-v-batch-head')).toHaveLength(0)
    expect(view.container.querySelectorAll('.w02-pagination')).toHaveLength(0)
  })

  it('uses a Material accordion with the first pending Material expanded', async () => {
    const user = userEvent.setup()
    renderW02()
    await user.click(await screen.findByRole('tab', { name: '待核实' }))
    const wood = screen.getByRole('button', { name: /木材.*项待核实/ })
    const metal = screen.getByRole('button', { name: /金属.*项待核实/ })
    expect(wood.getAttribute('aria-expanded')).toBe('true')
    expect(metal.getAttribute('aria-expanded')).toBe('false')
    await user.click(metal)
    expect(metal.getAttribute('aria-expanded')).toBe('true')
  })

  it('renders the fixed Search marker, formal statuses, and approved secondary actions', async () => {
    const user = userEvent.setup()
    const view = renderW02()
    await user.click(await screen.findByRole('tab', { name: '待核实' }))
    expect(view.container.querySelectorAll('.w02-v-field-icon').length).toBeGreaterThan(0)
    expect(screen.getAllByText('待核实').length).toBeGreaterThan(0)
    expect(screen.getAllByText('无法现场确认').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /去核实/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: /查看详情/ })).toBeTruthy()

    await user.selectOptions(screen.getByLabelText('状态筛选'), 'all')
    await user.selectOptions(screen.getByLabelText('材料筛选'), '金属')
    expect(view.container.querySelector('.w02-v-status.verified')?.textContent).toBe('已核实')
    await user.selectOptions(screen.getByLabelText('材料筛选'), '植栽')
    expect(view.container.querySelector('.w02-v-status.not_applicable')?.textContent).toBe('不适用')
  })

  it('navigates from W02-B using canonical batch_id and review-verification context', async () => {
    const user = userEvent.setup()
    renderW02()
    await user.click(await screen.findByRole('tab', { name: '待核实' }))
    await user.click(screen.getByRole('button', { name: /去核实/ }))

    expect(screen.getByLabelText('current-route').textContent).toBe('/workspace/batches/fixture-batch-wood')
    const state = screen.getByLabelText('navigation-state').textContent ?? ''
    expect(state).toContain('"source":"review-verification"')
    expect(state).toContain('"batch_id":"fixture-batch-wood"')
    expect(state).toContain('"source_tab":"review-verification"')
    expect(state).toContain('"expanded_material":"木材"')
    expect(state).toContain('"focus_target":"fixing_method"')
  })

  it('shows the W02-B filtered empty state while retaining search focus behavior', async () => {
    const user = userEvent.setup()
    renderW02()
    await user.click(await screen.findByRole('tab', { name: '待核实' }))
    const search = screen.getByLabelText('搜索待核实事项') as HTMLInputElement
    await user.type(search, '不存在的核实事项')
    expect(document.activeElement).toBe(search)
    expect(screen.getByText('没有符合当前筛选条件的核实事项')).toBeTruthy()
  })

  it('returns from W02 to W01 through the shared Workspace navigation', async () => {
    const user = userEvent.setup()
    renderW02()
    await user.click(await screen.findByRole('button', { name: '再生视图' }))
    expect(screen.getByLabelText('current-route').textContent).toBe(ImplementationRoutes.w01)
    expect(await screen.findByRole('heading', { name: '再生视图' })).toBeTruthy()
  })

  it('uses the shared Workspace header action to return to W01', async () => {
    const user = userEvent.setup()
    const view = renderW02()
    await waitFor(() => expect(view.container.querySelector('.workspace-header')).not.toBeNull())

    expect(view.container.querySelectorAll('.workspace-header')).toHaveLength(1)
    const action = view.container.querySelector('.w02-view-entry') as HTMLButtonElement | null
    expect(action).not.toBeNull()
    await user.click(action!)
    expect(screen.getByLabelText('current-route').textContent).toBe(ImplementationRoutes.w01)
  })
})
