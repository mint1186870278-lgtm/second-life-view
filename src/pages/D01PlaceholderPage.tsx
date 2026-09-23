import { useLocation, useParams } from 'react-router-dom'
import type { D01NavigationContext } from '../navigation'

export function D01PlaceholderPage() {
  const { batchId } = useParams()
  const location = useLocation()
  const context = location.state as D01NavigationContext | null

  return (
    <main className="development-placeholder" aria-labelledby="d01-placeholder-title">
      <strong>D01</strong>
      <h1 id="d01-placeholder-title">AssessmentBatch Detail / Human Verification</h1>
      <p>D01 正式内容不属于 Phase 1C；以下信息仅用于验证 typed navigation context。</p>
      <dl className="development-context">
        <div><dt>batch_id</dt><dd>{batchId ?? '未提供'}</dd></div>
        <div><dt>source</dt><dd>{context?.source ?? 'direct'}</dd></div>
        <div><dt>scene_id</dt><dd>{context?.source === 'view' ? context.return_state.scene_id : '—'}</dd></div>
        <div><dt>viewer_mode</dt><dd>{context?.source === 'view' ? context.return_state.viewer_mode : '—'}</dd></div>
        <div><dt>zoom_level</dt><dd>{context?.source === 'view' ? context.return_state.zoom_level ?? '—' : '—'}</dd></div>
        <div><dt>focus_target</dt><dd>{context?.focus_target ?? '—'}</dd></div>
      </dl>
    </main>
  )
}
