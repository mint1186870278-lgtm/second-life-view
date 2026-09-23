import type { W01DemoProjection } from '../selectors/w01Selectors'

export const w01DemoSceneAssetUrls: Readonly<Record<string, string>> = {
  'fixture-scene-roof': '/demo-assets/0552569a06b61e4551697bd0f211286e.jpg',
  'fixture-scene-lounge': '/demo-assets/371eefc93daaebc61d98fb6ed1422691.jpg',
  'fixture-scene-entry': '/demo-assets/d8bdc5c3e1e88f3672da35df425cca3c.jpg',
  'fixture-scene-service': '/demo-assets/combination_room.jpg',
}

/**
 * Non-authoritative W01 visual projection. Placement and unresolved summary/group
 * rows are demo presentation only and must never become domain derivation rules.
 */
export const w01DemoProjection: W01DemoProjection = {
  hotspot_placements: [
    { batch_id: 'fixture-batch-wood', x_percent: 9, y_percent: 39, tone: 'amber' },
    { batch_id: 'fixture-batch-metal', x_percent: 57, y_percent: 46, tone: 'green' },
  ],
  hotspot_rows: [
    { presentation_id: 'roof-wood', scene_id: 'fixture-scene-roof', batch_id: 'fixture-batch-wood', label: '木质围栏', quantity: 6, x_percent: 9, y_percent: 39, tone: 'amber' },
    { presentation_id: 'roof-planter', scene_id: 'fixture-scene-roof', label: '花池', quantity: 8, x_percent: 35, y_percent: 64, tone: 'green' },
    { presentation_id: 'roof-rail', scene_id: 'fixture-scene-roof', label: '栏杆', quantity: 3, x_percent: 58, y_percent: 60, tone: 'blue' },
    { presentation_id: 'roof-metal', scene_id: 'fixture-scene-roof', label: '金属面板', quantity: 4, x_percent: 66, y_percent: 45, tone: 'blue' },
    { presentation_id: 'lounge-deck', scene_id: 'fixture-scene-lounge', label: '户外地板', quantity: 1, x_percent: 30, y_percent: 63, tone: 'amber' },
    { presentation_id: 'lounge-metal', scene_id: 'fixture-scene-lounge', batch_id: 'fixture-batch-metal', label: '木质围栏', quantity: 2, x_percent: 57, y_percent: 46, tone: 'green' },
    { presentation_id: 'entry-metal', scene_id: 'fixture-scene-entry', label: '金属面板', quantity: 4, x_percent: 42, y_percent: 46, tone: 'blue' },
    { presentation_id: 'entry-rail', scene_id: 'fixture-scene-entry', label: '栏杆', quantity: 3, x_percent: 58, y_percent: 58, tone: 'amber' },
    { presentation_id: 'service-metal', scene_id: 'fixture-scene-service', label: '金属面板', quantity: 4, x_percent: 35, y_percent: 48, tone: 'blue' },
    { presentation_id: 'service-glass', scene_id: 'fixture-scene-service', label: '玻璃隔断', quantity: 8, x_percent: 57, y_percent: 56, tone: 'green' },
  ],
  task_rows: [
    { label: '确认固定方式', tone: 'amber', focus_target: 'fixing_method' },
    { label: '确认表面涂层', tone: 'blue', focus_target: 'surface_treatment' },
    { label: '检查隐藏损伤', tone: 'amber', focus_target: 'hidden_damage' },
    { label: '核实候选渠道', tone: 'gray', focus_target: 'local_opportunity' },
  ],
  detected_component_count: 41,
  coarse_summary: [
    { label: '保留', value: '12', tone: 'green' },
    { label: '复用', value: '18', tone: 'blue' },
    { label: '待确认', value: '7', tone: 'amber' },
    { label: '回收', value: '4', tone: 'gray' },
  ],
  group_rows: [
    { label: '木质围栏', quantity_label: '× 6', tone: 'wood' },
    { label: '花池', quantity_label: '× 8', tone: 'planter' },
    { label: '户外地板', quantity_label: '× 1', tone: 'deck' },
    { label: '金属面板', quantity_label: '× 4', tone: 'metal' },
    { label: '栏杆', quantity_label: '× 3', tone: 'rail' },
    { label: '草坪', quantity_label: '× 2', tone: 'grass' },
  ],
  potential: { value: '30', copy: '件构件，值得在拆除前再看一眼。' },
  filmstrip_fillers: [{ label: '后勤区', tone: 4 }],
}
