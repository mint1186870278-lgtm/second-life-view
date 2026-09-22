import type {
  AssessmentBatchId,
  EvidenceStatus,
  ReviewStatus,
  SceneId,
  VerificationStatus,
  VerificationType,
} from '../domain'

export type D01Source = 'view' | 'review-draft' | 'review-verification'
export type W01ViewerMode = 'site' | 'regeneration'
export type W02DraftSummaryFilter = 'all' | 'reviewed' | 'attention'

interface SharedReturnState {
  scroll_y?: number
  focus_target?: string
}

export interface W01ReturnState extends SharedReturnState {
  scene_id: SceneId
  viewer_mode: W01ViewerMode
  zoom_level?: number
  /** Opaque technical state; it must not be interpreted as new product behavior. */
  viewer_state?: Readonly<Record<string, unknown>>
}

export interface W02DraftReturnState extends SharedReturnState {
  source_tab: 'review-draft'
  summary_filter: W02DraftSummaryFilter
  material_filter: string | 'all'
  scene_filter: SceneId | 'all'
  evidence_filter: EvidenceStatus | 'all'
  review_filter: ReviewStatus | 'all'
  search: string
  /** Optional because the final pagination strategy is not frozen. */
  page?: number
}

export interface W02VerificationReturnState extends SharedReturnState {
  source_tab: 'review-verification'
  material_filter: string | 'all'
  scene_filter: SceneId | 'all'
  verification_type_filter: VerificationType | 'all'
  verification_status_filter: VerificationStatus | 'active' | 'all'
  search: string
  expanded_material: string | null
}

interface D01ContextBase {
  batch_id: AssessmentBatchId
  focus_target?: string
}

export type D01NavigationContext =
  | (D01ContextBase & { source: 'view'; return_state: W01ReturnState })
  | (D01ContextBase & { source: 'review-draft'; source_tab: 'review-draft'; return_state: W02DraftReturnState })
  | (D01ContextBase & {
      source: 'review-verification'
      source_tab: 'review-verification'
      return_state: W02VerificationReturnState
    })

/** Deferred Product Closure identifiers only. These are not routes or workflows. */
export type DeferredDestination =
  | '360-evidence-viewer'
  | 'pathway-detail'
  | 'reference-source-detail'
  | 'local-opportunity-detail'

export interface DeferredNavigationTarget {
  destination: DeferredDestination
  batch_id: AssessmentBatchId
}
