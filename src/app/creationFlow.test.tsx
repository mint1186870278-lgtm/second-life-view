// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { demoProjectOptionSource } from '../config'
import { PATHWAYS } from '../domain'
import { App } from './App'
import { ImplementationRoutes } from './routes'

afterEach(cleanup)

function LocationProbe() {
  const location = useLocation()
  return <output aria-label="current-route">{location.pathname}</output>
}

function renderRoute(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  )
}

describe('Phase 1B Creation Flow', () => {
  it('keeps prototype options in a fixture provider rather than formal domain enums', () => {
    expect(demoProjectOptionSource.regionOptions.length).toBeGreaterThan(0)
    expect(PATHWAYS).not.toContain(demoProjectOptionSource.projectTypeOptions[0].value)
  })

  it('validates C01 required fields and does not advance when invalid', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c01)
    const name = await screen.findByDisplayValue('HSBC MKK')
    await user.clear(name)
    await user.click(screen.getByRole('button', { name: '下一步：素材接入' }))
    expect((await screen.findByRole('alert')).textContent).toContain('请输入项目名称')
    expect(screen.getByLabelText('current-route').textContent).toContain(ImplementationRoutes.c01)
    await Promise.resolve()
    expect((name as HTMLInputElement).value).toBe('')
    expect(screen.getByLabelText('current-route').textContent).toContain(ImplementationRoutes.c01)
  })

  it('navigates from valid C01 state to C02', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c01)
    expect((await screen.findByDisplayValue('HSBC MKK') as HTMLInputElement).value).toBe('HSBC MKK')
    await user.click(screen.getByRole('button', { name: '下一步：素材接入' }))
    expect(await screen.findByRole('heading', { name: '现场素材接入' })).toBeTruthy()
    expect(screen.getByLabelText('current-route').textContent).toContain(ImplementationRoutes.c02)
  })

  it('renders the approved received-state composition and supports Scene rename', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })
    expect(screen.getAllByText('已接入')).toHaveLength(5)

    await user.click(screen.getByRole('button', { name: '重命名 屋顶花园' }))
    const input = screen.getByLabelText('场景 1 名称')
    await user.clear(input)
    await user.type(input, '屋顶花园（更新）')
    await user.click(screen.getByRole('button', { name: '保存场景名称' }))
    expect(screen.getByText(/屋顶花园（更新）/)).toBeTruthy()
  })

  it('supports C02 back and forward navigation', async () => {
    const user = userEvent.setup()
    const view = renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })
    await user.click(screen.getByRole('button', { name: '返回上一步' }))
    expect(await screen.findByRole('heading', { name: '新建再生评估项目' })).toBeTruthy()
    view.unmount()

    renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })
    await user.click(screen.getByRole('button', { name: '开始分析' }))
    expect(await screen.findByRole('heading', { name: '分析处理完成' })).toBeTruthy()
  })

  it('renders C03 selector-derived metrics and enters W01', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c03)
    await screen.findByRole('heading', { name: '分析处理完成' })

    const labels = ['已识别构件', '待核实事项', '评估草案']
    const values = ['4', '2', '1']
    labels.forEach((label, index) => {
      const card = screen.getByText(label).closest('.metric-card')
      expect(card).not.toBeNull()
      expect(within(card as HTMLElement).getByText(values[index])).toBeTruthy()
    })

    await user.click(screen.getByRole('button', { name: '进入再生视图' }))
    expect(await screen.findByRole('heading', { name: '再生视图' })).toBeTruthy()
    expect(screen.getByLabelText('current-route').textContent).toContain(ImplementationRoutes.w01)
  })

  it.each([
    [ImplementationRoutes.c01, '新建再生评估项目'],
    [ImplementationRoutes.c02, '现场素材接入'],
    [ImplementationRoutes.c03, '分析处理完成'],
    [ImplementationRoutes.w01, '再生视图'],
  ])('renders route %s', async (route, heading) => {
    renderRoute(route)
    expect(await screen.findByRole('heading', { name: heading })).toBeTruthy()
  })
})
