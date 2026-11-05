// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-configuration
//   version: 5
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-11-05"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Validate the persistence target configuration before opening a connection or performing migration work.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-main
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-migration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-restore-verifier
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts

import { readFileSync } from "node:fs";
import { posix } from "node:path";
import { postgreSqlLoginNameRule, postgreSqlPasswordCredentials } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { configReasonNames as configurationReasons, parseConfigJsonObject, recordConfigSource, validateConfigSettings, type ConfigSettingDefinition, type ConfigSettingIssue, type ConfigSettingRelationship } from "@kanbien/core/config";
import { loadPlatformConfiguration, configurationDiagnostic, defineConfigurationDiagnostic, defineConfigurationSourceReadDiagnostic, configurationSourceReadDiagnosticRecord, defineConfigurationRelationshipDiagnostics, configurationRelationshipDiagnostic } from "@kanbien/platform-config";
import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, diagnosticProcessingDefinition, requireDiagnosticRecord, parseDiagnosticRecord, parseRelatedDiagnosticRecords, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformSecurityDiagnosticCatalog, validateCertificateAuthorityContent } from "@kanbien/platform-security";
import { platformPersistenceDiagnosticCatalog, persistenceMaintenanceDiagnosticCatalog,
  validatePersistenceMigrationInstructions, validatePersistenceVerificationInstructions,
  type PersistenceInstructionCheck, type PersistenceExpectedRecordInput } from "@kanbien/platform-persistence";
import { platformObservabilityDiagnosticCatalog } from "@kanbien/platform-observability";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { bindPlatformDiagnosticContext } from "@kanbien/platform-contracts";

import { selectPersistenceImplementation, persistenceImplementationDiagnostic, type KanbienCorePersistenceImplementation } from "./kanbien-core-server-persistence-composition";

export const persistenceConfigurationBindings = {
  "database.host": "PERSISTENCE_POSTGRES_HOST", "database.port": "PERSISTENCE_POSTGRES_PORT",
  "database.name": "PERSISTENCE_POSTGRES_DATABASE", "database.schema": "PERSISTENCE_POSTGRES_SCHEMA",
  "authentication.reference": "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE",
  "administrator.reference": "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE",
} as const;
const configurationV1Reasons = [
  configurationReasons.missing, configurationReasons.blank, configurationReasons.surroundingWhitespace,
  configurationReasons.wrongType, configurationReasons.invalidFormat, configurationReasons.invalidInteger,
  configurationReasons.outOfRange, configurationReasons.inconsistentSettings,
] as const;
const administratorCredentialV1Reasons = [
  configurationReasons.missing, configurationReasons.blank, configurationReasons.surroundingWhitespace,
  configurationReasons.wrongType, configurationReasons.invalidFormat, configurationReasons.invalidInteger,
  configurationReasons.outOfRange, configurationReasons.inconsistentSettings,
  configurationReasons.invalidJson, configurationReasons.wrongShape, configurationReasons.empty, configurationReasons.forbiddenCharacter,
] as const;
export const persistenceConfigurationDiagnostic = defineConfigurationDiagnostic("kanbien-core-server.configuration-invalid", Object.keys(persistenceConfigurationBindings), configurationV1Reasons);
export const persistenceIamConfigurationDiagnostic = defineConfigurationDiagnostic("kanbien-core-server.iam-configuration-invalid", ["authentication.username", "authentication.region"], configurationV1Reasons);
export const persistenceAdministratorCredentialBindings = { "administrator.credentials": "PERSISTENCE_ADMINISTRATOR_CREDENTIALS" } as const;
export const persistenceAdministratorCredentialDiagnostic = defineConfigurationDiagnostic("kanbien-core-server.administrator-credentials-invalid", ["administrator.credentials", "administrator.username", "administrator.password"], administratorCredentialV1Reasons);
export const persistenceAdministrationBindings = {
  "migration.username": "PERSISTENCE_MIGRATION_DATABASE_USERNAME",
  "runtime.username": "PERSISTENCE_RUNTIME_DATABASE_USERNAME",
  "administration.operation": "PERSISTENCE_ADMINISTRATION_OPERATION",
} as const;
export const persistenceAdministrationOperations = ["bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"] as const;
export type PersistenceAdministrationOperation = typeof persistenceAdministrationOperations[number];
export const persistenceAdministrationRelationships = [
  { relationship: "administrator-migration-separation", rule: "must-differ", left: "administrator.username", right: "migration.username" },
  { relationship: "administrator-runtime-separation", rule: "must-differ", left: "administrator.username", right: "runtime.username" },
  { relationship: "migration-runtime-separation", rule: "must-differ", left: "migration.username", right: "runtime.username" },
] as const satisfies readonly ConfigSettingRelationship[];
export const persistenceAdministrationDiagnostics = defineConfigurationRelationshipDiagnostics("kanbien-core-server.administration-configuration-invalid",
  ["administrator.username", ...Object.keys(persistenceAdministrationBindings)], persistenceAdministrationRelationships, configurationV1Reasons);
export const persistenceCertificateSourceDiagnostic = defineDiagnostic({ code: "kanbien-core-server.certificate-source-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    source: { type: "enum", values: ["database.tls.authority-source"] },
    reason: { type: "enum", values: ["missing", "wrong-type", "blank", "surrounding-whitespace", "location-not-allowed", "path-not-normalized", "extension-not-allowed"] },
    phase: { type: "enum", values: ["configuration-source-validation"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);
export const persistenceCertificateReadDiagnostic = defineConfigurationSourceReadDiagnostic("kanbien-core-server.certificate-source-read-failed", ["database.tls.authority-source"]);
export const persistenceConfigurationDiagnosticCatalog = { owner: "kanbien-core-server", definitions: [persistenceImplementationDiagnostic, persistenceConfigurationDiagnostic, persistenceIamConfigurationDiagnostic, persistenceAdministratorCredentialDiagnostic, persistenceCertificateSourceDiagnostic, persistenceCertificateReadDiagnostic, ...persistenceAdministrationDiagnostics.definitions] } as const;
export const persistenceTaskConfigurationDiagnosticCatalog = { owner: "kanbien-core-server", definitions: [...persistenceConfigurationDiagnosticCatalog.definitions, ...persistenceMaintenanceDiagnosticCatalog.definitions] } as const;
const persistenceSourceDefinitions = [...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions];
const taskDiagnosticDefinitions = [...persistenceConfigurationDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions, ...persistenceSourceDefinitions, ...platformObservabilityDiagnosticCatalog.definitions];
export const persistenceStartupDiagnosticBinding = bindPlatformDiagnosticContext(
  { capability: 'persistence', operation: 'startup', stage: 'startup' },
  [...persistenceConfigurationDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions, ...platformObservabilityDiagnosticCatalog.definitions, diagnosticProcessingDefinition()],
);
/** Revalidate the exact selected catalog before serializing a task envelope. */
export function persistenceTaskDiagnosticFields(diagnostic?: DiagnosticRecord, relatedDiagnosticRecords?: readonly DiagnosticRecord[]) {
  try {
  const code = diagnostic === undefined ? undefined : Object.getOwnPropertyDescriptor(diagnostic, "code");
  const version = diagnostic === undefined ? undefined : Object.getOwnPropertyDescriptor(diagnostic, "definitionVersion");
  const definition = code && "value" in code && version && "value" in version ? taskDiagnosticDefinitions.find((item) => item.code === code.value && item.version === version.value) : undefined;
  const primary = definition === undefined ? undefined : parseDiagnosticRecord<unknown>(definition, diagnostic);
  const peerDefinitions = platformSecurityDiagnosticCatalog.definitions.filter((item) => item.code === "security.peer-identity-verification-failed" || item.code === "security.peer-trust-verification-failed");
  const permitsRelated = primary?.ok && persistenceSourceDefinitions.some((item) => item.code === primary.value.code && item.version === primary.value.definitionVersion);
  const tlsPrimary = primary?.ok && primary.value.code === "persistence.trust-validation-failed" && (primary.value.detail as { classification?: unknown }).classification === "tls_trust_invalid";
  const related = !permitsRelated || relatedDiagnosticRecords === undefined ? undefined
    : parseRelatedDiagnosticRecords([...persistenceSourceDefinitions, ...(tlsPrimary ? peerDefinitions : [])], relatedDiagnosticRecords);
  return { ...(primary?.ok ? { diagnostic: primary.value } : {}), ...(permitsRelated && related?.ok && related.value.length > 0 ? { related_diagnostics: related.value } : {}) };
  } catch { return {}; }
}

export function persistenceConfigurationFailure(issues: readonly ConfigSettingIssue[], definition = persistenceConfigurationDiagnostic) {
  const diagnostic = requireDiagnosticRecord([definition], captureDiagnosticRecord(() => {
    const checked = configurationDiagnostic(definition, issues);
    return checked.ok ? checked.value : undefined;
  }));
  return { ok: false as const, error: { code: "CONFIGURATION_INVALID" as const, diagnostic } };
}

export function persistenceConfigurationResult(env: NodeJS.ProcessEnv, purpose: "server" | "migration" | "restore" | "administration", implementation?: KanbienCorePersistenceImplementation) {
  const selected = implementation === undefined ? selectPersistenceImplementation(env["PERSISTENCE_IMPLEMENTATION"]) : { ok: true as const, value: implementation };
  if (!selected.ok) return selected;
  const reference = purpose === "administration" ? "administrator.reference" : "authentication.reference";
  const bindings = Object.fromEntries(selected.value.requirements.map(({ setting }) => [
    setting, persistenceConfigurationBindings[(setting === "authentication.reference" ? reference : setting) as keyof typeof persistenceConfigurationBindings],
  ]));
  const parsed = loadPlatformConfiguration({
    requirements: selected.value.requirements,
    bindings,
    source: recordConfigSource(env),
    assemble: values => selected.value.assembleConfiguration(values, {
      maximumPoolSize: purpose === "server" ? 4 : 1,
      // Migration and restoration are bounded operations whose declared
      // completion work can legitimately exceed a server readiness window.
      connectionTimeoutMs: purpose === "server" ? 5_000 : 30_000, idleTimeoutMs: 10_000,
      statementTimeoutMs: purpose === "migration" || purpose === "administration" ? 240_000 : purpose === "restore" ? 30_000 : 5_000,
      tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
    }),
  });
  if (!parsed.ok) {
    if (parsed.error.code === "CONFIGURATION_INVALID") return persistenceConfigurationFailure(parsed.error.issues.map(issue => ({
      ...issue, setting: issue.setting === "authentication.reference" ? reference : issue.setting,
    })));
    const fields: Record<string, string> = { host: "database.host", port: "database.port", database: "database.name", schema: "database.schema", runtimeCredentialSecretReference: reference };
    const setting = fields[parsed.error.details.path];
    if (setting === undefined) throw new TypeError("PERSISTENCE_CONFIGURATION_POLICY_INVALID");
    return persistenceConfigurationFailure([{ setting, reason: parsed.error.details.reasonCode }]);
  }
  return parsed;
}

export function persistenceConfiguration(env: NodeJS.ProcessEnv, purpose: "server" | "migration" | "restore") {
  // Compatibility reader; production entrypoints consume the structured result.
  const checked = persistenceConfigurationResult(env, purpose);
  return checked.ok ? checked.value : undefined;
}

export function persistenceCredentialsResult(value: unknown) {
  const parsed = parseConfigJsonObject(value);
  if (!parsed.ok) return persistenceConfigurationFailure([{ setting: "administrator.credentials", reason: parsed.error.reason }], persistenceAdministratorCredentialDiagnostic);
  const checked = postgreSqlPasswordCredentials(parsed.value);
  return checked.ok ? checked : persistenceConfigurationFailure(checked.error.issues.map(({ field, reason }) => ({ setting: `administrator.${field}`, reason })), persistenceAdministratorCredentialDiagnostic);
}

export function persistenceCredentials(value: unknown) {
  // Compatibility reader delegates to the same parser and provider rules.
  const checked = persistenceCredentialsResult(value);
  return checked.ok ? checked.value : undefined;
}

/** The caller supplies only the username from already validated administrator credentials. */
export function persistenceAdministrationConfigurationResult(env: NodeJS.ProcessEnv, administratorUsername: string) {
  const operation = env[persistenceAdministrationBindings["administration.operation"]];
  const definitions = [
    { setting: "administrator.username", source: "administrator.username", rule: postgreSqlLoginNameRule },
    { setting: "migration.username", source: persistenceAdministrationBindings["migration.username"], rule: postgreSqlLoginNameRule },
    { setting: "runtime.username", source: persistenceAdministrationBindings["runtime.username"], rule: postgreSqlLoginNameRule },
    { setting: "administration.operation", source: persistenceAdministrationBindings["administration.operation"],
      rule: { kind: "text", pattern: new RegExp(`^(?:${persistenceAdministrationOperations.join("|")})$`) } },
  ] as const satisfies readonly ConfigSettingDefinition[];
  // Do not copy the credential-bearing environment into this validation source.
  const source = recordConfigSource({
    "administrator.username": administratorUsername,
    PERSISTENCE_MIGRATION_DATABASE_USERNAME: env[persistenceAdministrationBindings["migration.username"]],
    PERSISTENCE_RUNTIME_DATABASE_USERNAME: env[persistenceAdministrationBindings["runtime.username"]],
    PERSISTENCE_ADMINISTRATION_OPERATION: operation === undefined ? "bootstrap-identities" : operation,
  });
  const checked = validateConfigSettings(source, definitions, persistenceAdministrationRelationships);
  if (!checked.ok) {
    const diagnostic = requireDiagnosticRecord(persistenceAdministrationDiagnostics.definitions, captureDiagnosticRecord(() => {
      const record = configurationRelationshipDiagnostic(persistenceAdministrationDiagnostics, checked.error);
      return record.ok ? record.value : undefined;
    }));
    return { ok: false as const, error: { ...checked.error, diagnostic } };
  }
  return { ok: true as const, value: {
    migration: { username: checked.value["migration.username"] as string },
    runtime: { username: checked.value["runtime.username"] as string },
    operation: checked.value["administration.operation"] as PersistenceAdministrationOperation,
  } };
}

export function persistenceCertificateAuthority(env: NodeJS.ProcessEnv): string | undefined {
  const checked = persistenceCertificateAuthorityResult(env);
  return checked.ok ? checked.value : undefined;
}

export function persistenceCertificateAuthorityResult(env: NodeJS.ProcessEnv, read: (path: string) => string = (path) => readFileSync(path, "utf8")) {
  const source = "database.tls.authority-source" as const;
  const path: unknown = env["PERSISTENCE_POSTGRES_CA_PATH"];
  const reason = path === undefined ? "missing" : typeof path !== "string" ? "wrong-type"
    : path.trim() === "" ? "blank" : path.trim() !== path ? "surrounding-whitespace"
    : !path.startsWith("/app/assets/") ? "location-not-allowed"
    : posix.normalize(path) !== path ? "path-not-normalized" : !path.endsWith(".crt") ? "extension-not-allowed" : undefined;
  if (reason !== undefined) {
    const diagnostic = requireDiagnosticRecord([persistenceCertificateSourceDiagnostic], captureDiagnosticRecord(() => {
      const checked = createDiagnosticRecord(persistenceCertificateSourceDiagnostic, { source, reason, phase: "configuration-source-validation", effect: "not-started" });
      return checked.ok ? checked.value : undefined;
    }));
    return { ok: false as const, error: { diagnostic } };
  }
  let value: string;
  try {
    value = read(path as string);
  } catch (error) {
    let code: unknown;
    try { if (typeof error === "object" && error !== null) { const field = Object.getOwnPropertyDescriptor(error, "code"); if (field && "value" in field) code = field.value; } } catch { /* unknown observation */ }
    const readReason = code === "ENOENT" ? "not-found" : code === "EACCES" || code === "EPERM" ? "read-denied"
      : code === "ENOTDIR" ? "not-a-directory" : code === "EISDIR" ? "is-a-directory" : "unclassified-read-failure";
    return { ok: false as const, error: { diagnostic: requireDiagnosticRecord([persistenceCertificateReadDiagnostic], captureDiagnosticRecord(() => configurationSourceReadDiagnosticRecord(persistenceCertificateReadDiagnostic, source, readReason))) } };
  }
  const parsed = validateCertificateAuthorityContent(value, "compatible-complete-blocks");
  if (!parsed.ok) return { ok: false as const, error: { diagnostic: parsed.error.diagnosticRecord } };
  return { ok: true as const, value };
}

export const persistenceMaintenanceBindings = Object.freeze({
  "migration.operation": "PERSISTENCE_MIGRATION_OPERATION",
  "verification.mode": "PERSISTENCE_RESTORE_DIAGNOSTIC_MODE",
  "verification.expected-record-id": "PERSISTENCE_ACCEPTANCE_RECORD_ID",
  "verification.expected-fingerprint": "PERSISTENCE_ACCEPTANCE_FACT_DIGEST",
});
const checkMaintenanceInstructions: PersistenceInstructionCheck = (source, requirements) => loadPlatformConfiguration({
  source, requirements,
  bindings: Object.fromEntries(requirements.map(({ setting }) => [setting, setting])),
  assemble: value => ({ ok: true, value }),
});
export function persistenceMigrationInstructionsResult(env: NodeJS.ProcessEnv) {
  return validatePersistenceMigrationInstructions(env[persistenceMaintenanceBindings["migration.operation"]], checkMaintenanceInstructions);
}
export function persistenceVerificationModeInput(env: NodeJS.ProcessEnv): unknown {
  return env[persistenceMaintenanceBindings["verification.mode"]];
}
export function persistenceExpectedRecordInput(env: NodeJS.ProcessEnv): PersistenceExpectedRecordInput {
  return {
    "verification.expected-record-id": env[persistenceMaintenanceBindings["verification.expected-record-id"]],
    "verification.expected-fingerprint": env[persistenceMaintenanceBindings["verification.expected-fingerprint"]],
  };
}
export function persistenceVerificationInstructionsResult(mode: unknown, expected: PersistenceExpectedRecordInput) {
  return validatePersistenceVerificationInstructions(mode, expected, checkMaintenanceInstructions);
}

export function environmentText(env: NodeJS.ProcessEnv, key: string): string | undefined {
  const value = env[key];
  return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined;
}
