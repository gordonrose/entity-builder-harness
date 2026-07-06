import { messageDescriptor, type MessageDescriptor, type MessageKey, type MessageParams } from "../shared/index";

export type ValidationPath = readonly string[];

export interface ValidationIssue extends MessageDescriptor {
  readonly path: ValidationPath;
}

export type NonEmptyValidationIssues = readonly [ValidationIssue, ...ValidationIssue[]];

export interface ValidValidationResult {
  readonly valid: true;
  readonly issues: readonly [];
}

export interface InvalidValidationResult {
  readonly valid: false;
  readonly issues: NonEmptyValidationIssues;
}

export type ValidationResult = ValidValidationResult | InvalidValidationResult;

export interface Validator<TValue> {
  validate(value: unknown): value is TValue;
  explain(value: unknown): ValidationResult;
}

export const validResult: ValidValidationResult = {
  valid: true,
  issues: [],
};

export function validationIssue(input: {
  readonly path?: ValidationPath;
  readonly code: string;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
}): ValidationIssue {
  return {
    path: [...(input.path ?? [])],
    ...messageDescriptor(input),
  };
}

export function invalidResult(issue: ValidationIssue): InvalidValidationResult;
export function invalidResult(issues: NonEmptyValidationIssues): InvalidValidationResult;
export function invalidResult(input: ValidationIssue | NonEmptyValidationIssues): InvalidValidationResult {
  if (isValidationIssueList(input)) {
    const [firstIssue, ...remainingIssues] = input;

    return {
      valid: false,
      issues: [firstIssue, ...remainingIssues],
    };
  }

  return {
    valid: false,
    issues: [input],
  };
}

function isValidationIssueList(input: ValidationIssue | NonEmptyValidationIssues): input is NonEmptyValidationIssues {
  return Array.isArray(input);
}

export function isValid(result: ValidationResult): result is ValidValidationResult {
  return result.valid;
}

export function isInvalid(result: ValidationResult): result is InvalidValidationResult {
  return !result.valid;
}

export function combineValidationResults(results: readonly ValidationResult[]): ValidationResult {
  const issues = results.flatMap((result) => result.issues);

  if (issues.length === 0) {
    return validResult;
  }

  return invalidResult(issues as unknown as NonEmptyValidationIssues);
}

export function withValidationPathPrefix(prefix: ValidationPath, issue: ValidationIssue): ValidationIssue {
  return {
    ...issue,
    path: [...prefix, ...issue.path],
  };
}
