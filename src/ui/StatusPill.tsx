import type { SceneIngestionStatus } from '../domain'

const sceneStatusPresentation: Record<SceneIngestionStatus, { label: string; tone: string }> = {
  waiting: { label: '等待接入', tone: 'neutral' },
  receiving: { label: '接收中', tone: 'info' },
  received: { label: '已接入', tone: 'success' },
  ingestion_error: { label: '接入异常', tone: 'error' },
}

export function getSceneIngestionPresentation(status: SceneIngestionStatus) {
  return sceneStatusPresentation[status]
}

export function SceneIngestionStatusPill({ status }: { status: SceneIngestionStatus }) {
  const presentation = getSceneIngestionPresentation(status)
  return (
    <span className={`status-pill status-pill--${presentation.tone}`}>
      <span className="status-pill__dot" />
      {presentation.label}
    </span>
  )
}
