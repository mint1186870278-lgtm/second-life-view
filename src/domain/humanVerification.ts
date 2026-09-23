export const HUMAN_VERIFICATION_FIELD_KEYS = [
  'fixing_method',
  'hidden_damage',
  'surface_treatment',
] as const

export type HumanVerificationFieldKey = (typeof HUMAN_VERIFICATION_FIELD_KEYS)[number]

export const HUMAN_VERIFICATION_FIELD_LABELS: Record<HumanVerificationFieldKey, string> = {
  fixing_method: '固定方式',
  hidden_damage: '隐藏腐朽',
  surface_treatment: '表面处理',
}

export function isHumanVerificationFieldKey(value: unknown): value is HumanVerificationFieldKey {
  return typeof value === 'string'
    && HUMAN_VERIFICATION_FIELD_KEYS.includes(value as HumanVerificationFieldKey)
}
