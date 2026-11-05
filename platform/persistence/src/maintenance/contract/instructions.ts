import type { ConfigSettingRequirement, ConfigSettingsFailure, ConfigSource } from "@kanbien/core/config";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Result } from "@kanbien/core/shared";
import { persistenceAcceptanceProof } from "./acceptance-proof";

export const persistenceMigrationRequirements = Object.freeze([
  Object.freeze({ setting: "migration.operation", rule: Object.freeze({ kind: "choice", values: Object.freeze(["apply"]) }) }),
] as const satisfies readonly ConfigSettingRequirement[]);
export const persistenceVerificationModeRequirements = Object.freeze([
  Object.freeze({ setting: "verification.mode", rule: Object.freeze({ kind: "choice", values: Object.freeze(["connection"]) }) }),
] as const satisfies readonly ConfigSettingRequirement[]);
export const persistenceExpectedRecordRequirements = Object.freeze([
  Object.freeze({ setting: "verification.expected-record-id", rule: persistenceAcceptanceProof.recordId }),
  Object.freeze({ setting: "verification.expected-fingerprint", rule: persistenceAcceptanceProof.fingerprint }),
] as const satisfies readonly ConfigSettingRequirement[]);

export type PersistenceInstructionCheck = (source: ConfigSource, requirements: readonly ConfigSettingRequirement[]) => Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure>;
export interface PersistenceInstructionFailure { readonly code: "CONFIGURATION_INVALID"; readonly diagnostic: DiagnosticRecord }
export interface PersistenceMigrationInstructions { readonly operation: "apply" }
export type PersistenceVerificationInstructions = { readonly mode: "connection" }
  | { readonly mode: "verify-record"; readonly expected: { readonly recordId: string; readonly factDigest: string } };
export type PersistenceExpectedRecordInput = Readonly<Record<"verification.expected-record-id" | "verification.expected-fingerprint", unknown>>;
