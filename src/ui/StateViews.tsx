import { AlertTriangle, Inbox, LoaderCircle } from 'lucide-react'
import { Button } from './Button'

export function LoadingState({ label = '正在加载…' }: { label?: string }) {
  return (
    <div className="system-state" role="status">
      <LoaderCircle className="system-state__spinner" />
      <strong>{label}</strong>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="system-state system-state--error" role="alert">
      <AlertTriangle />
      <strong>加载失败</strong>
      <span>{message}</span>
      {onRetry && <Button variant="secondary" onClick={onRetry}>重新加载</Button>}
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="system-state">
      <Inbox />
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  )
}
