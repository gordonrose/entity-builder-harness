import { configurationDiagnostic, validateConfigRequirements, type ConfigValue, type ConfigSettingIssue } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { persistenceMigrationRequirements, persistenceVerificationModeRequirements, persistenceExpectedRecordRequirements,
  type PersistenceInstructionCheck, type PersistenceInstructionFailure, type PersistenceMigrationInstructions,
  type PersistenceVerificationInstructions, type PersistenceExpectedRecordInput } from "../../contract/instructions";
import { persistenceMigrationInstructionsDiagnostic, persistenceVerificationInstructionsDiagnostic } from "../../contract/reporting/diagnostics";

export function persistenceConnectionDiagnosticMode(input: unknown): boolean {
  return input === persistenceVerificationModeRequirements[0].rule.values[0];
}

export function validatePersistenceMigrationInstructions(operation: unknown, check: PersistenceInstructionCheck = validateConfigRequirements): Result<PersistenceMigrationInstructions, PersistenceInstructionFailure> {
  const checked = check({ get: () => (operation === undefined ? persistenceMigrationRequirements[0].rule.values[0] : operation) as ConfigValue }, persistenceMigrationRequirements);
  return checked.ok ? { ok: true, value: { operation: checked.value["migration.operation"] as "apply" } }
    : failure(persistenceMigrationInstructionsDiagnostic, checked.error.issues);
}

export function validatePersistenceVerificationInstructions(mode: unknown, expected: PersistenceExpectedRecordInput,
  check: PersistenceInstructionCheck = validateConfigRequirements): Result<PersistenceVerificationInstructions, PersistenceInstructionFailure> {
  // Preserve the existing optional-mode interpretation; ignored modes are not diagnosed as rejected inputs.
  const present = typeof mode === "string" && mode.trim() !== "" && mode.trim() === mode;
  if (present) {
    const checked = check({ get: () => mode }, persistenceVerificationModeRequirements);
    if (!checked.ok) return failure(persistenceVerificationInstructionsDiagnostic, checked.error.issues);
    return { ok: true, value: { mode: checked.value["verification.mode"] as "connection" } };
  }
  const checked = check({ get: name => expected[name as keyof PersistenceExpectedRecordInput] as ConfigValue }, persistenceExpectedRecordRequirements);
  return checked.ok ? { ok: true, value: { mode: "verify-record", expected: {
    recordId: checked.value["verification.expected-record-id"] as string,
    factDigest: checked.value["verification.expected-fingerprint"] as string,
  } } } : failure(persistenceVerificationInstructionsDiagnostic, checked.error.issues);
}

function failure(definition: typeof persistenceMigrationInstructionsDiagnostic, issues: readonly ConfigSettingIssue[]): Result<never, PersistenceInstructionFailure> {
  const diagnostic = configurationDiagnostic(definition, issues);
  if (!diagnostic.ok) throw new TypeError("PERSISTENCE_INSTRUCTION_DIAGNOSTIC_INVALID");
  return { ok: false, error: { code: "CONFIGURATION_INVALID", diagnostic: diagnostic.value } };
}
