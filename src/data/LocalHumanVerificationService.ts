import type {
  HumanVerificationService,
  SubmitHumanVerificationDraftCommand,
  SubmitHumanVerificationDraftResult,
} from '../application'

/**
 * Phase 1E session-local adapter. It acknowledges a verification draft but owns
 * no canonical Project data and makes no claim about durable backend persistence.
 */
export class LocalHumanVerificationService implements HumanVerificationService {
  async submitDraft(
    command: SubmitHumanVerificationDraftCommand,
  ): Promise<SubmitHumanVerificationDraftResult> {
    return {
      batch_id: command.batch_id,
      component_instance_id: command.component_instance_id,
      accepted_draft: {
        values: { ...command.draft.values },
        note: command.draft.note.trim(),
      },
    }
  }
}

export const d01HumanVerificationService = new LocalHumanVerificationService()
