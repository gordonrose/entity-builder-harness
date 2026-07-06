import {
  invalidResult,
  isInvalid,
  isValid,
  validationIssue,
  validResult,
  type InvalidValidationResult,
  type ValidationIssue,
  type ValidationPath,
  type ValidationResult,
  type ValidValidationResult,
} from "../src/validation/index";

const path: ValidationPath = ["profile", "email"];
const issue = validationIssue({
  path,
  code: "INVALID_EMAIL",
  defaultMessage: "Email is invalid.",
  messageKey: "validation.invalid_email",
  params: { field: "email" },
});

const acceptedIssue: ValidationIssue = issue;
void acceptedIssue;

const acceptedValid: ValidValidationResult = validResult;
void acceptedValid;

const acceptedInvalid: InvalidValidationResult = invalidResult(issue);
void acceptedInvalid;

// @ts-expect-error invalid validation results must have at least one issue.
invalidResult([]);

// @ts-expect-error validation issues require fallback/default text, not only a code.
validationIssue({ path, code: "MISSING_DEFAULT_MESSAGE" });

// @ts-expect-error validation params must stay localization-friendly primitives.
validationIssue({ path, code: "BAD_PARAM", defaultMessage: "Bad param.", params: { nested: { value: "nope" } } });

// @ts-expect-error valid results cannot be assigned to invalid results.
const rejectedInvalid: InvalidValidationResult = validResult;
void rejectedInvalid;

const result: ValidationResult = Math.random() > 0.5 ? validResult : invalidResult(issue);

if (isValid(result)) {
  const issues: readonly [] = result.issues;
  void issues;
}

if (isInvalid(result)) {
  const firstIssue: ValidationIssue = result.issues[0];
  void firstIssue;
}
