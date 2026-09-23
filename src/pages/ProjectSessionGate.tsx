import type { ReactNode } from 'react'
import { useProjectSession } from '../app/ProjectSessionContext'
import { ErrorState, LoadingState } from '../ui'

export function ProjectSessionGate({ children }: { children: ReactNode }) {
  const { status, errorMessage, reload } = useProjectSession()
  if (status === 'loading') return <LoadingState label="正在加载项目…" />
  if (status === 'error') return <ErrorState message={errorMessage ?? '项目数据加载失败'} onRetry={reload} />
  return children
}
