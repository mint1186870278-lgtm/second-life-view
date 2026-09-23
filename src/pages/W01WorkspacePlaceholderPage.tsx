import { Construction } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useProjectSession } from '../app/ProjectSessionContext'
import {
  getWorkspaceDestinationRoute,
  WORKSPACE_NAVIGATION_ITEMS,
} from '../app/workspaceNavigation'
import { WorkspaceShell } from '../ui'
import { ProjectSessionGate } from './ProjectSessionGate'

export function W01WorkspacePlaceholderPage() {
  return (
    <ProjectSessionGate><W01WorkspacePlaceholderContent /></ProjectSessionGate>
  )
}

function W01WorkspacePlaceholderContent() {
  const { project } = useProjectSession()
  const navigate = useNavigate()
  return (
    <WorkspaceShell
      projectName={project?.name ?? '当前项目'}
      items={WORKSPACE_NAVIGATION_ITEMS}
      activeDestination="view"
      onNavigate={(destination) => navigate(getWorkspaceDestinationRoute(destination))}
    >
      <section className="workspace-placeholder">
        <span><Construction size={28} /></span>
        <p className="workspace-placeholder__eyebrow">W01</p>
        <h1>再生视图</h1>
        <p>Workspace shell 已连接。360 Viewer、热点、分组投影与 Regeneration Potential 将在产品边界明确后实现。</p>
      </section>
    </WorkspaceShell>
  )
}
