import type { W01ViewerMode } from '../../navigation'
import type { W01DemoProjection } from '../../selectors'

export function ViewerModeSwitch({
  mode,
  onChange,
}: {
  mode: W01ViewerMode
  onChange: (mode: W01ViewerMode) => void
}) {
  return (
    <div className="w01-mode-switch" aria-label="视图模式">
      <button
        type="button"
        className={mode === 'site' ? 'is-active' : ''}
        aria-pressed={mode === 'site'}
        onClick={() => onChange('site')}
      >
        现场视图
      </button>
      <button
        type="button"
        className={mode === 'regeneration' ? 'is-active' : ''}
        aria-pressed={mode === 'regeneration'}
        onClick={() => onChange('regeneration')}
      >
        再生视图
      </button>
    </div>
  )
}

export function W01SidebarSupplement({
  demoProjection,
}: {
  demoProjection: W01DemoProjection
}) {
  return (
    <div className="w01-sidebar-supplement">
      <div className="w01-sidebar-divider" />
      <p className="w01-sidebar-kicker">已识别构件</p>
      <div className="w01-component-total">
        <strong>{demoProjection.detected_component_count}</strong><span>个构件</span>
      </div>
      <div className="w01-coarse-summary" data-authority="demo-only">
        {demoProjection.coarse_summary.map((row) => (
          <div className="w01-coarse-row" key={row.label}>
            <span className={`w01-tone-dot is-${row.tone}`} />
            <span>{row.label}</span>
            <strong>{row.value}</strong>
          </div>
        ))}
      </div>
      <div className="w01-sidebar-divider w01-sidebar-divider--groups" />
      <div className="w01-sidebar-section-title">构件分组</div>
      <div className="w01-demo-groups" data-authority="demo-only">
        {demoProjection.group_rows.map((row) => (
          <div className="w01-demo-group" key={row.label}>
            <span className={`w01-group-swatch is-${row.tone}`} />
            <span>{row.label}</span>
            <small>{row.quantity_label}</small>
          </div>
        ))}
      </div>
    </div>
  )
}
