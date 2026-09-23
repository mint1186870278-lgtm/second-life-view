import type {
  AssessmentBatchId,
  ComponentInstanceId,
  HumanVerificationFieldKey,
} from '../domain'

export interface HumanVerificationDraft {
  values: Record<HumanVerificationFieldKey, string | null>
  note: string
}

export interface SubmitHumanVerificationDraftCommand {
  batch_id: AssessmentBatchId
  component_instance_id: ComponentInstanceId
  draft: HumanVerificationDraft
}

export interface SubmitHumanVerificationDraftResult {
  batch_id: AssessmentBatchId
  component_instance_id: ComponentInstanceId
  accepted_draft: HumanVerificationDraft
}

/**
 * Application boundary for D01 human input.
 * It intentionally promises no backend persistence or assessment recalculation semantics.
 */
export interface HumanVerificationService {
  submitDraft(command: SubmitHumanVerificationDraftCommand): Promise<SubmitHumanVerificationDraftResult>
}
