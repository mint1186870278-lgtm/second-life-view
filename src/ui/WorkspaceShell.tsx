import { ChevronDown, Plus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { BrandLockup } from './BrandMark'
import { Button } from './Button'

export function ProjectContextSwitcher({ projectName }: { projectName: string }) {
  return (
    <button className="project-context" type="button" aria-label="当前项目" disabled>
      <span>
        <strong>{projectName}</strong>
        <small>当前项目</small>
      </span>
      <ChevronDown size={18} />
    </button>
  )
}

export function WorkspaceGlobalHeader({ projectName }: { projectName: string }) {
  return (
    <header className="workspace-header">
      <BrandLockup />
      <div />
      <div className="workspace-header__actions">
        <ProjectContextSwitcher projectName={projectName} />
        <Button variant="primary" disabled title="新建项目入口将在后续阶段连接">
          <Plus size={17} /> 新建项目
        </Button>
      </div>
    </header>
  )
}

export type WorkspaceDestination = 'view' | 'review'

export interface WorkspaceNavigationItem {
  destination: WorkspaceDestination
  label: string
  icon: LucideIcon
}

interface WorkspaceSidebarProps {
  items: readonly WorkspaceNavigationItem[]
  activeDestination: WorkspaceDestination
  onNavigate: (destination: WorkspaceDestination) => void
}

export function WorkspaceSidebar({ items, activeDestination, onNavigate }: WorkspaceSidebarProps) {
  return (
    <aside className="workspace-sidebar">
      <nav aria-label="工作区导航">
        {items.map(({ destination, label, icon: Icon }) => {
          const isActive = destination === activeDestination
          return (
            <button
              className={`workspace-nav-item ${isActive ? 'is-active' : ''}`.trim()}
              type="button"
              key={destination}
              aria-current={isActive ? 'page' : undefined}
              onClick={() => onNavigate(destination)}
            >
              <Icon size={21} />
              {label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

interface WorkspaceShellProps extends WorkspaceSidebarProps {
  projectName: string
  children: ReactNode
}

export function WorkspaceShell({
  projectName,
  items,
  activeDestination,
  onNavigate,
  children,
}: WorkspaceShellProps) {
  return (
    <div className="app-frame workspace-frame">
      <WorkspaceGlobalHeader projectName={projectName} />
      <div className="workspace-body">
        <WorkspaceSidebar
          items={items}
          activeDestination={activeDestination}
          onNavigate={onNavigate}
        />
        <main className="workspace-content">{children}</main>
      </div>
    </div>
  )
}
