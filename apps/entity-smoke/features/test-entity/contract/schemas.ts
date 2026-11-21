import { isoDateTime, uuid } from "@kanbien/core/shared";
import { invalidResult, validResult, validationIssue, type ValidationIssue, type ValidationResult, type Validator } from "@kanbien/core/validation";
import { testEntityValidationRecord } from "./diagnostics";
import type { CreateTestEntityInput, TestEntityCategory, TestEntityStatus, UpdateTestEntityInput } from "./types";

const statuses = new Set<TestEntityStatus>(["draft", "active", "closed"]);
const categories = new Set<TestEntityCategory>(["alpha", "beta", "gamma"]);
const fields = ["integerValue", "uuidValue", "occurredAt", "label", "status", "enabled", "categories", "notes", "description", "reviewedAt", "secondaryCategories"] as const;
type Field = typeof fields[number];

export const createTestEntitySchema: Validator<CreateTestEntityInput> = schema(false) as Validator<CreateTestEntityInput>;
export const updateTestEntitySchema: Validator<UpdateTestEntityInput> = schema(true) as Validator<UpdateTestEntityInput>;

function schema(isUpdate: boolean): Validator<CreateTestEntityInput | UpdateTestEntityInput> {
  return {
    validate(value): value is CreateTestEntityInput | UpdateTestEntityInput { return explain(value, isUpdate).valid; },
    explain(value): ValidationResult { return explain(value, isUpdate); },
    diagnose(value) {
      const result = explain(value, isUpdate);
      if (result.valid) return undefined;
      const issue = result.issues[0];
      const field = issue.path[0] ?? "input";
      return testEntityValidationRecord(field as Field | "input", reasonFor(issue));
    },
  };
}

function explain(value: unknown, isUpdate: boolean): ValidationResult {
  if (!isObject(value)) return invalidResult(validationIssue({ code: "TEST_ENTITY_INVALID", defaultMessage: "Expected an object.", path: [] }));
  const issues = fields.flatMap((field) => validateField(value, field, isUpdate));
  return issues.length === 0 ? validResult : invalidResult(issues as [typeof issues[0], ...typeof issues]);
}

function validateField(value: Record<string, unknown>, field: Field, isUpdate: boolean) {
  const present = Object.hasOwn(value, field);
  if (!present) return isUpdate ? [] : [issue(field, "missing", "A value is required.")];
  const input = value[field];
  if (field === "integerValue") return typeof input === "number" && Number.isSafeInteger(input) ? [] : [issue(field, "invalid-value", "Expected a safe integer.")];
  if (field === "uuidValue") return typeof input === "string" && uuid(input).ok ? [] : [issue(field, "invalid-format", "Expected a valid UUID.")];
  if (field === "occurredAt") return typeof input === "string" && isoDateTime(input).ok ? [] : [issue(field, "invalid-format", "Expected a valid ISO date-time.")];
  if (field === "label") return typeof input === "string" && input.trim().length > 0 && input.length <= 200 ? [] : [issue(field, "invalid-value", "Expected a non-empty label of at most 200 characters.")];
  if (field === "status") return typeof input === "string" && statuses.has(input as TestEntityStatus) ? [] : [issue(field, "invalid-value", "Expected a supported status.")];
  if (field === "enabled") return typeof input === "boolean" ? [] : [issue(field, "wrong-type", "Expected a boolean.")];
  if (field === "categories" || field === "secondaryCategories") {
    if (input === null && field === "secondaryCategories") return [];
    return validCategoryArray(input) ? [] : [issue(field, Array.isArray(input) ? "invalid-item" : "wrong-type", "Expected supported category entries.")];
  }
  if (field === "notes") return validTextArray(input) ? [] : [issue(field, Array.isArray(input) ? "invalid-item" : "wrong-type", "Expected text entries.")];
  if (field === "description") return input === null || typeof input === "string" ? [] : [issue(field, "wrong-type", "Expected text or null.")];
  if (field === "reviewedAt") return input === null || typeof input === "string" && isoDateTime(input).ok ? [] : [issue(field, "invalid-format", "Expected an ISO date-time or null.")];
  return [];
}

function issue(field: Field, reason: string, defaultMessage: string) { return validationIssue({ code: "TEST_ENTITY_INVALID_ATTRIBUTE", defaultMessage, path: [field], params: { reason } }); }
function validCategoryArray(value: unknown): value is readonly TestEntityCategory[] { return Array.isArray(value) && value.every((item) => typeof item === "string" && categories.has(item as TestEntityCategory)); }
function validTextArray(value: unknown): value is readonly string[] { return Array.isArray(value) && value.every((item) => typeof item === "string" && item.length <= 500); }
function isObject(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value); }
function reasonFor(issue: ValidationIssue): "missing" | "wrong-type" | "invalid-format" | "invalid-value" | "invalid-item" {
  if (issue.code === "TEST_ENTITY_INVALID") return "wrong-type";
  const reason = issue.params?.reason;
  if (reason === "missing" || reason === "wrong-type" || reason === "invalid-format" || reason === "invalid-value" || reason === "invalid-item") return reason;
  throw new TypeError("TEST_ENTITY_VALIDATION_REASON_INVALID");
}
