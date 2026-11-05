import type { Result } from "../../../shared/index";
import type { ConfigSource, ConfigSettingRule, ConfigSettingRequirement, ConfigSettingDefinition, ConfigSettingRelationship } from "../../contract/types";
import type { ConfigSettingsFailure, ConfigSettingsRelationshipFailure } from "../../contract/reporting/errors";
import type { ConfigRelationshipIssue, ConfigSettingIssue } from "../../contract/reporting/setting-issues";
import { captureDiagnosticRecord, createDiagnosticRecord, requireDiagnosticRecord } from "../../../diagnostics/index";
import { attachCoreDiagnosticRecord } from "../../../shared/index";
import { coreConfigDeclarationDiagnostic, coreConfigRelationshipDeclarationDiagnostic, coreConfigSourceDiagnostic, coreConfigSourceRecord, coreConfigChoiceDeclarationDiagnostic } from "../../contract/reporting/diagnostics";


const nativeDeclarationSome = Array.prototype.some;
const applyDeclarationSome = Reflect.apply;

function declarationSome<TValue>(value: readonly TValue[], some: unknown, callback: (item: TValue, index?: unknown) => boolean, label: "definitions" | "relationships"): unknown {
  if (typeof some !== "function") {
    if (label === "definitions") {
      const definitions = { some: some as (visit: typeof callback) => unknown };
      return definitions.some(callback);
    }
    const relationships = { some: some as (visit: typeof callback) => unknown };
    return relationships.some(callback);
  }
  return applyDeclarationSome(some, value, [callback]);
}
function declarationPosition(some: unknown, index: unknown): number | undefined {
  return some === nativeDeclarationSome && typeof index === "number" && Number.isSafeInteger(index) && index >= 0 && index <= 31 ? index : undefined;
}

/** Values stay private; error detail contains only declared logical names and reasons. */
export function validateConfigSettings(source: ConfigSource, definitions: readonly ConfigSettingDefinition[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure>;
export function validateConfigSettings<const TDefinitions extends readonly ConfigSettingDefinition[]>(source: ConfigSource, definitions: TDefinitions,
  relationships: readonly ConfigSettingRelationship<NoInfer<TDefinitions[number]["setting"]>>[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsRelationshipFailure>;
export function validateConfigSettings(source: ConfigSource, definitions: readonly ConfigSettingDefinition[], relationships?: readonly ConfigSettingRelationship[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure | ConfigSettingsRelationshipFailure> {
  const values: Record<string, string | number> = {};
  const issues: ConfigSettingIssue[] = [];
  const choices = new Map<ConfigSettingRule, readonly string[]>();
  if (definitions.length === 0) rejectDeclaration("definitions", "empty");
  if (definitions.length > 32) rejectDeclaration("definitions", "too-many");
  const names = definitions.map((item) => item.setting);
  if (new Set(names).size !== definitions.length) rejectDeclaration("setting", "identity-count-mismatch");
  const definitionsSome: unknown = definitions.some;
  let declarationObservation: { field: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["field"]; reason: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["reason"]; index?: number } | undefined;
  const observeDeclaration = (field: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["field"], reason: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["reason"], index?: number): true => {
    declarationObservation ??= { field, reason, ...(index === undefined ? {} : { index }) }; return true;
  };
  if (declarationSome(definitions, definitionsSome, (item, claimedIndex: unknown = undefined) => {
    const index = declarationPosition(definitionsSome, claimedIndex);
    if (!/^[a-z][a-z0-9.-]{0,127}$/.test(item.setting)) return observeDeclaration("setting", "invalid-format", index);
    if (!/^[A-Za-z][A-Za-z0-9_.-]{0,127}$/.test(item.source)) return observeDeclaration("source", "invalid-format", index);
    if (["constructor", "prototype", "__proto__"].includes(item.setting)) return observeDeclaration("setting", "reserved", index);
    const ruleKind = item.rule.kind;
    if (ruleKind === "integer") {
      if (!Number.isSafeInteger(item.rule.minimum)) return observeDeclaration("minimum", "not-safe-integer", index);
      if (!Number.isSafeInteger(item.rule.maximum)) return observeDeclaration("maximum", "not-safe-integer", index);
      if (item.rule.minimum > item.rule.maximum) return observeDeclaration("bounds", "reversed", index);
    }
    if (ruleKind === "choice") choices.set(item.rule, checkedChoices(item.rule.values));
    return false;
  }, "definitions")) {
    if (definitionsSome === nativeDeclarationSome && declarationObservation !== undefined) {
      const { field, reason, index } = declarationObservation;
      rejectDeclaration(field, reason, index);
    }
    rejectDeclaration("definitions", "predicate-rejected-unclassified");
  }
  if (relationships !== undefined) {
    const settings = new Set(definitions.map(({ setting }) => setting));
    const pairs = new Set<string>();
    if (relationships.length > 32) rejectRelationshipDeclaration("relationships", "too-many");
    const names = relationships.map(({ relationship }) => relationship);
    if (new Set(names).size !== relationships.length) rejectRelationshipDeclaration("relationship", "identity-count-mismatch");
    const relationshipsSome: unknown = relationships.some;
    let relationshipObservation: { field: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["field"]; reason: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["reason"]; index?: number } | undefined;
    const observeRelationship = (field: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["field"], reason: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["reason"], index?: number): true => {
      relationshipObservation ??= { field, reason, ...(index === undefined ? {} : { index }) }; return true;
    };
    if (declarationSome(relationships, relationshipsSome, ({ relationship, rule, left, right }, claimedIndex: unknown = undefined) => {
        const index = declarationPosition(relationshipsSome, claimedIndex);
        const pair = JSON.stringify([left, right].sort());
        const duplicate = pairs.has(pair);
        pairs.add(pair);
        if (!/^[a-z][a-z0-9.-]{0,127}$/.test(relationship)) return observeRelationship("relationship", "invalid-format", index);
        if (rule !== "must-differ") return observeRelationship("rule", "unsupported", index);
        if (!settings.has(left)) return observeRelationship("left", "undeclared", index);
        if (!settings.has(right)) return observeRelationship("right", "undeclared", index);
        if (left === right) return observeRelationship("participants", "self-reference", index);
        if (duplicate) return observeRelationship("participants", "duplicate-pair", index);
        return false;
      }, "relationships")) {
      if (relationshipsSome === nativeDeclarationSome && relationshipObservation !== undefined) {
        const { field, reason, index } = relationshipObservation;
        rejectRelationshipDeclaration(field, reason, index);
      }
      rejectRelationshipDeclaration("relationships", "predicate-rejected-unclassified");
    }
  }

  let definitionIndex = 0;
  for (const { setting, source: sourceKey, rule } of definitions) {
    let raw;
    try { raw = source.get(sourceKey); }
    catch (error) { throw attachCoreDiagnosticRecord(error, requireDiagnosticRecord([coreConfigSourceDiagnostic], captureDiagnosticRecord(() => coreConfigSourceRecord("schema", definitionIndex)))); }
    definitionIndex++;
    const issue = (reason: ConfigSettingIssue["reason"]) => issues.push({ setting, reason });
    if (raw === undefined) { issue("missing"); continue; }
    if (typeof raw !== "string") { issue("wrong-type"); continue; }
    if (raw.trim() === "") { issue("blank"); continue; }
    if (raw.trim() !== raw) { issue("surrounding-whitespace"); continue; }
    const ruleKind = rule.kind;
    if (ruleKind === "integer") {
      if (!/^-?\d+$/.test(raw)) { issue("invalid-integer"); continue; }
      const number = Number(raw);
      if (!Number.isSafeInteger(number) || number < rule.minimum || number > rule.maximum) { issue("out-of-range"); continue; }
      values[setting] = number;
    } else if (ruleKind === "choice") {
      if (!(choices.get(rule) ?? checkedChoices(rule.values)).includes(raw)) { issue("unsupported-value"); continue; }
      values[setting] = raw;
    } else {
      if (rule.pattern !== undefined) {
        const pattern = new RegExp(rule.pattern.source, rule.pattern.flags.replace(/[gy]/g, ""));
        if (!pattern.test(raw)) { issue("invalid-format"); continue; }
      }
      values[setting] = raw;
    }
  }
  const relationshipIssues: ConfigRelationshipIssue[] = [];
  for (const relationship of relationships ?? []) {
    if (Object.hasOwn(values, relationship.left) && Object.hasOwn(values, relationship.right)
      && values[relationship.left] === values[relationship.right]) relationshipIssues.push({ relationship: relationship.relationship,
        rule: relationship.rule, left: relationship.left, right: relationship.right });
  }
  return issues.length > 0 || relationshipIssues.length > 0
    ? { ok: false, error: { code: "CONFIGURATION_INVALID", issues, ...(relationships === undefined ? {} : { relationshipIssues }) } }
    : { ok: true, value: values };
}

function rejectDeclaration(field: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["field"], reason: NonNullable<typeof coreConfigDeclarationDiagnostic.__detail>["reason"], index?: number): never {
  const record = requireDiagnosticRecord([coreConfigDeclarationDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(coreConfigDeclarationDiagnostic, { field, reason, ...(index === undefined ? {} : { index }) });
    return checked.ok ? checked.value : undefined;
  }));
  const error = new TypeError("CONFIGURATION_SCHEMA_INVALID");
  throw attachCoreDiagnosticRecord(error, record);
}
function rejectRelationshipDeclaration(field: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["field"], reason: NonNullable<typeof coreConfigRelationshipDeclarationDiagnostic.__detail>["reason"], index?: number): never {
  const record = requireDiagnosticRecord([coreConfigRelationshipDeclarationDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(coreConfigRelationshipDeclarationDiagnostic, { field, reason, ...(index === undefined ? {} : { index }) });
    return checked.ok ? checked.value : undefined;
  }));
  const error = new TypeError("CONFIGURATION_RELATIONSHIP_SCHEMA_INVALID");
  throw attachCoreDiagnosticRecord(error, record);
}

/** Apply reusable requirements to a logical-name source; concrete bindings stay outside Core. */
export function validateConfigRequirements(source: ConfigSource, requirements: readonly ConfigSettingRequirement[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure>;
export function validateConfigRequirements<const TRequirements extends readonly ConfigSettingRequirement[]>(source: ConfigSource, requirements: TRequirements,
  relationships: readonly ConfigSettingRelationship<NoInfer<TRequirements[number]["setting"]>>[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsRelationshipFailure>;
export function validateConfigRequirements(source: ConfigSource, requirements: readonly ConfigSettingRequirement[], relationships?: readonly ConfigSettingRelationship[]): Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure | ConfigSettingsRelationshipFailure> {
  if (!Array.isArray(requirements)) rejectDeclaration("definitions", "predicate-rejected-unclassified");
  const definitions = requirements.map(item => {
    if (typeof item !== "object" || item === null || typeof item.rule !== "object" || item.rule === null
      || (item.rule.kind !== "text" && item.rule.kind !== "integer" && item.rule.kind !== "choice")) rejectDeclaration("definitions", "predicate-rejected-unclassified");
    return { setting: item.setting, source: item.setting, rule: item.rule };
  });
  return relationships === undefined ? validateConfigSettings(source, definitions) : validateConfigSettings(source, definitions, relationships);
}

function checkedChoices(input: readonly string[]): readonly string[] {
  const reject = (reason: NonNullable<typeof coreConfigChoiceDeclarationDiagnostic.__detail>["reason"], index?: number): never => {
    const record = requireDiagnosticRecord([coreConfigChoiceDeclarationDiagnostic], captureDiagnosticRecord(() => {
      const checked = createDiagnosticRecord(coreConfigChoiceDeclarationDiagnostic, { reason, ...(index === undefined ? {} : { index }) });
      return checked.ok ? checked.value : undefined;
    }));
    const error = new TypeError("CONFIGURATION_CHOICE_DECLARATION_INVALID");
    throw attachCoreDiagnosticRecord(error, record);
  };
  if (!Array.isArray(input)) reject("wrong-type");
  if (input.length === 0) reject("empty");
  if (input.length > 32) reject("too-many");
  const snapshot: string[] = [];
  for (let index = 0; index < input.length; index++) {
    const value: unknown = input[index];
    if (typeof value !== "string") reject("wrong-type", index);
    const text = value as string;
    if (text.trim() === "") reject("blank", index);
    if (text.trim() !== text) reject("surrounding-whitespace", index);
    if (snapshot.includes(text)) reject("duplicate", index);
    snapshot.push(text);
  }
  return Object.freeze(snapshot);
}
