import { describe, expect, it } from 'vitest'
import { SCENE_INGESTION_STATUSES } from '../domain'
import { getSceneIngestionPresentation } from './StatusPill'

describe('Scene ingestion presentation', () => {
  it('covers every formal SceneIngestionStatus without changing domain values', () => {
    expect(SCENE_INGESTION_STATUSES.map(getSceneIngestionPresentation)).toEqual([
      { label: '等待接入', tone: 'neutral' },
      { label: '接收中', tone: 'info' },
      { label: '已接入', tone: 'success' },
      { label: '接入异常', tone: 'error' },
    ])
  })
})
