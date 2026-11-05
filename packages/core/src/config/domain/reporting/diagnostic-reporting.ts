import { configReasonNames, type ConfigIssueReason } from "../../contract/reporting/setting-issues";
import { configSourceReadFailureReasons, type ConfigSourceReadFailureReason } from "../../contract/reporting/sourcing-issues";
import type { ConfigSettingRelationship } from "../../contract/types";
import type { ConfigSettingsRelationshipFailure } from "../../contract/reporting/errors";
import { recordConfigSource } from "../reading/source";
import { validateConfigSettings } from "../validation/settings";
import { createDiagnosticRecord, defineDiagnostic } from "../../../diagnostics/index";

// Retained optional-argument behaviour for existing callers, not a growing vocabulary.
const retainedV1ReasonSelection = [
  configReasonNames.missing, configReasonNames.blank, configReasonNames.surroundingWhitespace,
  configReasonNames.wrongType, configReasonNames.invalidFormat, configReasonNames.invalidInteger,
  configReasonNames.outOfRange, configReasonNames.inconsistentSettings,
] as const;

/** The caller supplies reviewed logical identifiers/reasons, never values.
 * Custom capability reasons are closed by that definition, not added to older
 * definitions or inferred from exception messages.
 */
export function defineConfigurationDiagnostic(code: string, settings: readonly string[], reasons: readonly string[] = retainedV1ReasonSelection) {
  return defineDiagnostic({ code, version: 1,
    classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: {
      issues: { type: "array", minItems: 1, maxItems: 32, items: { type: "object", properties: {
        setting: { type: "enum", values: settings }, reason: { type: "enum", values: reasons },
      } } },
    } },
  } as const);
}

export function configurationDiagnostic(definition: ReturnType<typeof defineConfigurationDiagnostic>, issues: readonly { readonly setting: string; readonly reason: string }[]) {
  return createDiagnosticRecord(definition, { issues });
}

/**
 * Additive configuration diagnostics for approved field and relationship checks.
 * Register every returned `definitions` entry with the owning catalog. Codes
 * append `.fields`, `.relationships` or `.fields-and-relationships`; each shape
 * requires nonempty evidence of its own kind. Historical field-only definitions
 * are not widened. Declarations map serialized relationship IDs back to logical
 * participants, never to supplied values or provider environment bindings.
 */
export function defineConfigurationRelationshipDiagnostics(code: string, settings: readonly string[], relationships: readonly ConfigSettingRelationship[], reasons: readonly ConfigIssueReason[] = retainedV1ReasonSelection) {
  // Validate the same declarations as runtime configuration, without reading values.
  validateConfigSettings(recordConfigSource({}), settings.map((setting) => ({ setting, source: setting, rule: { kind: "text" } })), relationships);
  if (relationships.length === 0) throw new TypeError("CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID");
  const declarations = Object.freeze(relationships.map(({ relationship, rule, left, right }) => Object.freeze({ relationship, rule, left, right })));
  const classification = { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" } as const;
  const issues = { type: "array", minItems: 1, maxItems: 32, items: { type: "object", properties: {
    setting: { type: "enum", values: settings }, reason: { type: "enum", values: reasons },
  } } } as const;
  const relationshipIssues = { type: "array", minItems: 1, maxItems: 32, items: { type: "object", properties: {
    relationship: { type: "enum", values: declarations.map(({ relationship }) => relationship) }, rule: { type: "enum", values: ["must-differ"] },
  } } } as const;
  const fields = defineDiagnostic({ code: `${code}.fields`, version: 1, classification, detail: { type: "object", properties: { issues } } } as const);
  const relations = defineDiagnostic({ code: `${code}.relationships`, version: 1, classification, detail: { type: "object", properties: { relationshipIssues } } } as const);
  const combined = defineDiagnostic({ code: `${code}.fields-and-relationships`, version: 1, classification, detail: { type: "object", properties: { issues, relationshipIssues } } } as const);
  return Object.freeze({ fields, relations, combined, declarations, definitions: Object.freeze([fields, relations, combined]) });
}

/** Only declared relationship IDs are serialized; compared values never enter records. */
export function configurationRelationshipDiagnostic(definitions: ReturnType<typeof defineConfigurationRelationshipDiagnostics>, failure: ConfigSettingsRelationshipFailure) {
  try {
    const evidence = relationshipEvidenceObject(failure, ["code", "issues", "relationshipIssues"]);
    if (evidence["code"] !== "CONFIGURATION_INVALID") throw new TypeError();
    // Bound and snapshot both arrays before traversing any caller-owned entries.
    const fieldEvidence = relationshipEvidenceArray(evidence["issues"]);
    const relationshipEvidence = relationshipEvidenceArray(evidence["relationshipIssues"]);
    const issues = fieldEvidence.map((issue) => {
      const fields = relationshipEvidenceObject(issue, ["setting", "reason"]);
      if (typeof fields["setting"] !== "string" || typeof fields["reason"] !== "string") throw new TypeError();
      return { setting: fields["setting"], reason: fields["reason"] as ConfigIssueReason };
    });
    const relationshipIssues = relationshipEvidence.map((issue) => {
      const fields = relationshipEvidenceObject(issue, ["relationship", "rule", "left", "right"]);
      const declaration = definitions.declarations.find((item) => item.relationship === fields["relationship"]);
      if (!declaration || declaration.rule !== fields["rule"] || declaration.left !== fields["left"] || declaration.right !== fields["right"]) throw new TypeError();
      return { relationship: declaration.relationship, rule: declaration.rule };
    });
    if (relationshipIssues.length === 0) return createDiagnosticRecord(definitions.fields, { issues });
    if (issues.length === 0) return createDiagnosticRecord(definitions.relations, { relationshipIssues });
    return createDiagnosticRecord(definitions.combined, { issues, relationshipIssues });
  } catch { throw new TypeError("CONFIGURATION_RELATIONSHIP_ISSUE_INVALID"); }
}

/** Structural guards for this public evidence boundary; never invoke accessors. */
function relationshipEvidenceObject(value: unknown, keys: readonly string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new TypeError();
  const prototype = Object.getPrototypeOf(value);
  const ownKeys = Reflect.ownKeys(value);
  if ((prototype !== Object.prototype && prototype !== null) || ownKeys.length !== keys.length
    || ownKeys.some((key) => typeof key !== "string" || !keys.includes(key))) throw new TypeError();
  const snapshot: Record<string, unknown> = {};
  for (const key of keys) {
    const field = Object.getOwnPropertyDescriptor(value, key);
    if (!field || !("value" in field) || !field.enumerable) throw new TypeError();
    snapshot[key] = field.value;
  }
  return snapshot;
}

function relationshipEvidenceArray(value: unknown): readonly unknown[] {
  if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) throw new TypeError();
  const length = Object.getOwnPropertyDescriptor(value, "length");
  if (!length || !("value" in length) || !Number.isInteger(length.value) || length.value < 0 || length.value > 32) throw new TypeError();
  if (Reflect.ownKeys(value).length !== length.value + 1) throw new TypeError();
  const snapshot: unknown[] = [];
  for (let index = 0; index < length.value; index += 1) {
    const item = Object.getOwnPropertyDescriptor(value, String(index));
    if (!item || !("value" in item) || !item.enumerable) throw new TypeError();
    snapshot.push(item.value);
  }
  return snapshot;
}

export function defineConfigurationSourceReadDiagnostic(code: string, sources: readonly string[]) { return defineDiagnostic({ code, version: 1,
  classification: { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["configuration-source-read"] },
    source: { type: "enum", values: sources },
    reason: { type: "enum", values: configSourceReadFailureReasons },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const); }
export function configurationSourceReadDiagnosticRecord(definition: ReturnType<typeof defineConfigurationSourceReadDiagnostic>, source: string, reason: ConfigSourceReadFailureReason) {
  const checked = createDiagnosticRecord(definition, { phase: "configuration-source-read", source, reason, effect: "not-assessed" });
  if (!checked.ok) throw new TypeError("PLATFORM_CONFIG_SOURCE_DIAGNOSTIC_INVALID");
  return checked.value;
}
