import { ClipboardCheck, RotateCcw } from 'lucide-react'
import { ImplementationRoutes } from './routes'
import type { WorkspaceDestination, WorkspaceNavigationItem } from '../ui'

/**
 * Product-authoritative Workspace entries with implementation-owned destinations.
 * Literal route strings remain isolated in ImplementationRoutes.
 */
export const WORKSPACE_NAVIGATION_ITEMS: readonly WorkspaceNavigationItem[] = [
  { destination: 'view', label: '再生视图', icon: RotateCcw },
  { destination: 'review', label: '项目审查', icon: ClipboardCheck },
]

export function getWorkspaceDestinationRoute(destination: WorkspaceDestination): string {
  return destination === 'view' ? ImplementationRoutes.w01 : ImplementationRoutes.w02
}
