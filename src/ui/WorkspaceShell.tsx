import { ChevronDown, MapPin, Plus, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { BrandLockup } from './BrandMark'
import { Button } from './Button'

export function ProjectContextSwitcher({
  projectName,
  contextLabel = '当前项目',
}: {
  projectName: string
  contextLabel?: string
}) {
  return (
    <button className="project-context" type="button" aria-label="当前项目" disabled>
      <span>
        <strong>{projectName}</strong>
        <small><MapPin size={15} />{contextLabel}</small>
      </span>
      <ChevronDown size={18} />
    </button>
  )
}

interface WorkspaceGlobalHeaderProps {
  projectName: string
  projectContextLabel?: string
  center?: ReactNode
  action?: ReactNode
}

export function WorkspaceGlobalHeader({
  projectName,
  projectContextLabel,
  center,
  action,
}: WorkspaceGlobalHeaderProps) {
  return (
    <header className="workspace-header">
      <BrandLockup />
      <div className="workspace-header__center">{center}</div>
      <div className="workspace-header__actions">
        <ProjectContextSwitcher projectName={projectName} contextLabel={projectContextLabel} />
        {action ?? (
          <Button variant="primary" disabled title="新建项目入口将在后续阶段连接">
            <Plus size={17} /> 新建项目
          </Button>
        )}
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
  frameClassName?: string
  projectName: string
  projectContextLabel?: string
  headerCenter?: ReactNode
  headerAction?: ReactNode
  sidebarSupplement?: ReactNode
  contentClassName?: string
  children: ReactNode
}

export function WorkspaceShell({
  projectName,
  projectContextLabel,
  headerCenter,
  headerAction,
  sidebarSupplement,
  frameClassName = '',
  contentClassName = '',
  items,
  activeDestination,
  onNavigate,
  children,
}: WorkspaceShellProps) {
  return (
    <div className={("app-frame workspace-frame " + frameClassName).trim()}>
      <WorkspaceGlobalHeader
        projectName={projectName}
        projectContextLabel={projectContextLabel}
        center={headerCenter}
        action={headerAction}
      />
      <div className="workspace-body">
        <div className="workspace-sidebar-column">
          <WorkspaceSidebar
            items={items}
            activeDestination={activeDestination}
            onNavigate={onNavigate}
          />
          {sidebarSupplement}
        </div>
        <main className={`workspace-content ${contentClassName}`.trim()}>{children}</main>
      </div>
    </div>
  )
}
