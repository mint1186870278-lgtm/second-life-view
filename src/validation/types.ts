export type InvariantCode =
  | 'DUPLICATE_ID'
  | 'INVALID_ENUM_VALUE'
  | 'MISSING_PROJECT_REFERENCE'
  | 'MISSING_SCENE_REFERENCE'
  | 'MISSING_BATCH_REFERENCE'
  | 'MISSING_COMPONENT_REFERENCE'
  | 'MISSING_VERIFICATION_REFERENCE'
  | 'PROJECT_REFERENCE_MISMATCH'
  | 'BATCH_SCENE_MISMATCH'
  | 'BATCH_QUANTITY_DRIFT'
  | 'BATCH_PENDING_COUNT_DRIFT'

export interface InvariantIssue {
  code: InvariantCode
  path: string
  message: string
}

export interface ValidationResult {
  valid: boolean
  issues: InvariantIssue[]
}

export class DomainInvariantError extends Error {
  readonly issues: InvariantIssue[]

  constructor(issues: InvariantIssue[]) {
    super(`Project graph violates ${issues.length} domain invariant(s).`)
    this.name = 'DomainInvariantError'
    this.issues = issues
  }
}
