import { configReasonNames as reason, defineConfigurationDiagnostic } from "@kanbien/core/config";

export const persistenceMigrationInstructionsDiagnostic = defineConfigurationDiagnostic("persistence.migration-instructions-invalid", ["migration.operation"],
  [reason.wrongType, reason.blank, reason.surroundingWhitespace, reason.unsupportedValue]);
export const persistenceVerificationInstructionsDiagnostic = defineConfigurationDiagnostic("persistence.verification-instructions-invalid",
  ["verification.mode", "verification.expected-record-id", "verification.expected-fingerprint"],
  [reason.missing, reason.wrongType, reason.blank, reason.surroundingWhitespace, reason.invalidFormat, reason.unsupportedValue]);
export const persistenceMaintenanceDiagnosticCatalog = Object.freeze({ owner: "platform.persistence.maintenance",
  definitions: Object.freeze([persistenceMigrationInstructionsDiagnostic, persistenceVerificationInstructionsDiagnostic]),
});
