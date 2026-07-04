export interface ValidationIssue {
  readonly path: readonly string[];
  readonly code: string;
  readonly message: string;
}

export interface ValidationResult {
  readonly valid: boolean;
  readonly issues: readonly ValidationIssue[];
}

export interface Validator<TValue> {
  validate(value: unknown): value is TValue;
  explain(value: unknown): ValidationResult;
}

export const validResult: ValidationResult = {
  valid: true,
  issues: [],
};
