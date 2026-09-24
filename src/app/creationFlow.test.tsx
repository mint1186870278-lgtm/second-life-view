// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { fallbackDemoScenes, type DemoAnalysisResult } from '../api/demo'
import { demoProjectOptionSource } from '../config'
import { PATHWAYS } from '../domain'
import { App } from './App'
import { ImplementationRoutes } from './routes'

const demoAnalysisResult: DemoAnalysisResult = {
  run_id: 'run_frontend_test',
  status: 'completed',
  scenes: fallbackDemoScenes.slice(0, 2),
  scene_count: 2,
  raw_detection_count: 85,
  component_count: 39,
  group_count: 2,
  category_counts: { cabinet: 2, chair: 20, sofa: 5, table: 12 },
  evidence_checked_count: 12,
  pending_evidence_count: 0,
  groups: [
    {
      id: 'roof-cabinet-01',
      group_name: '柜体组 01',
      label: 'Cabinet',
      category: 'cabinet',
      scene_id: fallbackDemoScenes[0].id,
      scene_name: fallbackDemoScenes[0].name,
      confidence: 0.94,
      detected_count: 2,
    },
    {
      id: 'lounge-chair-01',
      group_name: '座椅组 01',
      label: 'Chair',
      category: 'chair',
      scene_id: fallbackDemoScenes[1].id,
      scene_name: fallbackDemoScenes[1].name,
      confidence: 0.89,
      detected_count: 4,
    },
  ],
  groups_truncated: 0,
  design: {
    title: '保留结构的低碳翻新方案',
    rationale: '测试方案',
    prompt: '测试提示',
    constraints: ['保留原始结构'],
    status: 'draft',
  },
  spatial_generation: {
    status: 'mock',
    provider: 'aholo-spatial-gen',
    preview_url: fallbackDemoScenes[0].asset_url,
    message: '测试 Mock',
  },
  stages: {
    preprocess: { status: 'completed', provider: 'Aholo Spatial Gen', message: '预处理完成' },
    perception: { status: 'completed', provider: 'Perception Agent', message: '识别完成' },
    evidence: { status: 'completed', provider: 'Evidence Agent', message: '查证完成' },
    design: { status: 'draft', provider: 'Design Agent', message: '草案完成' },
  },
  sources: [],
  events: [],
  errors: [],
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
    const url = typeof input === 'string' ? input : input.toString()
    const body = url.endsWith('/api/v1/demo/scenes')
      ? { scenes: fallbackDemoScenes, source: 'test' }
      : demoAnalysisResult
    return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } })
  }))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

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

  it('renders repository panorama samples and supports scene selection', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })
    expect(await screen.findAllByText(/360° 已接入/)).toHaveLength(11)

    await user.click(screen.getByRole('button', { name: '取消选择 屋顶露台' }))
    expect(screen.getByRole('button', { name: '选择 屋顶露台' }).getAttribute('aria-pressed')).toBe('false')
  })

  it('captures through the Windows loopback gateway and displays Linux YOLO output', async () => {
    const captureResult = {
      asset: {
        image_url: 'https://linux.example.test/camera-assets/room.jpg',
        frame_id: 'frame-001',
        filename: 'room.jpg',
        size_bytes: 1234,
        source: 'windows_multipart',
      },
      yolo: {
        source: 'linux:yolov8s-worldv2',
        mode: 'live',
        detector: 'yolov8s-worldv2',
        device: '1',
        projection: 'equirectangular',
        annotation_kind: 'perspective_contact_sheet',
        raw_detection_count: 26,
        component_group_count: 16,
        annotated_image_url: 'https://linux.example.test/camera-assets/room-yolo.jpg',
        detections_url: 'https://linux.example.test/camera-assets/room-yolo.json',
      },
      run: { run_id: 'run_live_001', status: 'awaiting_evidence' },
      gateway: { frame_id: 'frame-001', filename: 'room.jpg' },
    }
    const fetchMock = vi.fn(async (input: string | URL | Request, _init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/v1/browser/capture-and-ingest')) {
        return new Response(JSON.stringify(captureResult), { status: 200, headers: { 'content-type': 'application/json' } })
      }
      const body = url.endsWith('/api/v1/demo/scenes')
        ? { scenes: fallbackDemoScenes, source: 'test' }
        : demoAnalysisResult
      return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } })
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })

    await user.click(screen.getByRole('button', { name: '采集现场照片' }))
    expect(await screen.findByRole('heading', { name: '已上传并完成在线推理' })).toBeTruthy()
    expect(screen.getByRole('img', { name: 'Linux YOLO 标注预览' }).getAttribute('src')).toBe(captureResult.yolo.annotated_image_url)
    expect(screen.getByText(/Linux YOLO：26 个检测框 · 16 组/)).toBeTruthy()

    const captureCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/v1/browser/capture-and-ingest'))
    expect(captureCall).toBeTruthy()
    const request = captureCall?.[1] as RequestInit
    expect(request.headers).toMatchObject({ 'X-Second-Life-Client': 'capture-ui-v1' })
    expect(JSON.parse(request.body as string)).not.toHaveProperty('detections')

    await user.click(screen.getByRole('button', { name: '确认' }))
    expect(await screen.findByText('26 个检测框 · Linux 在线推理')).toBeTruthy()
    expect(screen.getByText('YOLO 16 组')).toBeTruthy()
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
    await user.click(screen.getByRole('button', { name: '开始全链路分析' }))
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

  it('projects completed analysis into W01 annotations, groups, and the 3d regeneration dialog', async () => {
    const user = userEvent.setup()
    renderRoute(ImplementationRoutes.c02)
    await screen.findByRole('heading', { name: '现场素材接入' })
    await user.click(screen.getByRole('button', { name: '开始全链路分析' }))
    await screen.findByRole('heading', { name: '分析处理完成' })
    await user.click(screen.getByRole('button', { name: '进入再生视图' }))

    const annotatedImage = await screen.findByRole('img', { name: '屋顶露台 YOLO 标注图' })
    expect(annotatedImage.getAttribute('src')).toBe(fallbackDemoScenes[0].annotated_url)
    expect(screen.getByText('85')).toBeTruthy()
    expect(screen.getAllByText('39 组').length).toBeGreaterThan(0)
    expect(screen.getAllByText('柜体组 01').length).toBeGreaterThan(0)

    await user.click(screen.getByRole('button', { name: /场景 02.*大堂休息区/ }))
    expect(screen.getByRole('img', { name: '大堂休息区 YOLO 标注图' }).getAttribute('src')).toBe(fallbackDemoScenes[1].annotated_url)
    expect(screen.getByText('85')).toBeTruthy()
    expect(screen.getAllByText('39 组').length).toBeGreaterThan(0)
    expect(screen.getAllByText('座椅组 01').length).toBeGreaterThan(0)

    await user.click(screen.getByRole('button', { name: '3d再生' }))
    const dialog = screen.getByRole('dialog', { name: '3D再生' })
    const link = within(dialog).getByRole('link', { name: 'https://studio.aholo3d.cn/editor?projectId=3FO4K4XJJ82N' })
    expect(link.getAttribute('href')).toBe('https://studio.aholo3d.cn/editor?projectId=3FO4K4XJJ82N')
    expect(link.getAttribute('target')).toBe('_blank')
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
