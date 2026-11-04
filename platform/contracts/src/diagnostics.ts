import { parseDiagnosticRecord, validDiagnosticDefinition, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { CorrelationId, Result } from "@kanbien/core/shared";
import { withPlatformContractDiagnostic, type PlatformContractDiagnosticField, type PlatformContractDiagnosticCondition } from "./registration-diagnostics";
import type { PlatformContractError } from "./errors";

export interface PlatformDiagnosticCatalog { readonly owner: string; readonly definitions: readonly DiagnosticDefinition[] }
export interface PlatformDiagnosticContext {
  readonly correlationId?: CorrelationId;
  readonly capability: string;
  readonly operation: string;
  readonly stage: "configuration" | "startup" | "runtime" | "request" | "readiness" | "migration" | "recovery" | "shutdown";
}
export interface PlatformDiagnosticReporter {
  report(record: DiagnosticRecord, context: PlatformDiagnosticContext): { readonly status: "written" | "rejected" | "unavailable" };
}

/** Snapshot only permitted context fields; never read caller accessors. */
export function platformDiagnosticContext(value: unknown): PlatformDiagnosticContext | undefined {
  try {
    if (typeof value !== 'object' || value === null || Object.getPrototypeOf(value) !== Object.prototype) return undefined;
    const keys = Reflect.ownKeys(value).sort().join(',');
    const fields = Object.getOwnPropertyDescriptors(value);
    if ((keys !== 'capability,operation,stage' && keys !== 'capability,correlationId,operation,stage')
      || Object.values(fields).some(field => !('value' in field))) return undefined;
    const context = Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value])) as unknown as PlatformDiagnosticContext;
    if ((context.correlationId !== undefined && (typeof context.correlationId !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(context.correlationId)))
      || ![context.capability, context.operation].every(item => typeof item === 'string' && /^[a-z][a-z0-9.-]{0,127}$/.test(item))
      || !['configuration', 'startup', 'runtime', 'request', 'readiness', 'migration', 'recovery', 'shutdown'].includes(context.stage)) return undefined;
    return Object.freeze(context);
  } catch { return undefined; }
}

export interface PlatformDiagnosticContextBinding {
  select(record: DiagnosticRecord): { readonly record: DiagnosticRecord; readonly context: PlatformDiagnosticContext } | undefined;
}

/** Bind an owner's fixed operation to selected definitions before dependent work. */
export function bindPlatformDiagnosticContext(context: PlatformDiagnosticContext, definitions: readonly DiagnosticDefinition[]): PlatformDiagnosticContextBinding {
  const checked = platformDiagnosticContext(context);
  let selected: DiagnosticDefinition[];
  try {
    if (!checked || !Array.isArray(definitions) || Object.getPrototypeOf(definitions) !== Array.prototype
      || definitions.length === 0 || definitions.length > 256 || Reflect.ownKeys(definitions).length !== definitions.length + 1) throw new TypeError();
    const entries: DiagnosticDefinition[] = [];
    for (let index = 0; index < definitions.length; index++) {
      const item = Object.getOwnPropertyDescriptor(definitions, String(index));
      if (!item || !('value' in item) || !validDiagnosticDefinition(item.value)) throw new TypeError();
      entries.push(item.value);
    }
    if (new Set(entries.map(item => `${item.code}@${item.version}`)).size !== entries.length) throw new TypeError();
    selected = JSON.parse(JSON.stringify(entries)) as DiagnosticDefinition[];
  } catch { throw new TypeError('PLATFORM_DIAGNOSTIC_CONTEXT_BINDING_INVALID'); }
  const select: PlatformDiagnosticContextBinding['select'] = record => {
    for (const definition of selected) {
      const parsed = parseDiagnosticRecord(definition, record);
      if (parsed.ok) return Object.freeze({ record: parsed.value, context: checked! });
    }
    return undefined;
  };
  return Object.freeze({ select });
}

/** Pure registration validation shared by production and test registries. */
export function validatePlatformDiagnosticCatalog(value: PlatformDiagnosticCatalog, existing: readonly PlatformDiagnosticCatalog[] = []): Result<PlatformDiagnosticCatalog, PlatformContractError> {
  let field: PlatformContractDiagnosticField = "declaration";
  let condition: PlatformContractDiagnosticCondition = "declaration-rejected";
  let phase: "structure" | "definitions" | "conflicts" | "snapshot" = "structure";
  const reject = (location: PlatformContractDiagnosticField, reason: PlatformContractDiagnosticCondition): true => { field = location; condition = reason; return true; };
  const failure = (): Result<never, PlatformContractError> => {
    const result = invalid();
    if (result.ok) return result;
    return { ok: false, error: withPlatformContractDiagnostic(result.error, "diagnostic-catalog", field, condition, phase) };
  };
  try {
    if ((!value && reject("declaration", "object-required"))
      || (Object.getPrototypeOf(value) !== Object.prototype && reject("declaration", "plain-object-required"))
      || (Reflect.ownKeys(value).sort().join(",") !== "definitions,owner" && reject("declaration", "exact-fields-required"))
      || (Object.values(Object.getOwnPropertyDescriptors(value)).some((field) => !("value" in field)) && reject("declaration", "data-fields-required"))
      || (typeof value.owner !== "string" && reject("owner", "string-required"))
      || (value.owner.length > 128 && reject("owner", "owner-too-long"))
      || (!/^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/.test(value.owner) && reject("owner", "invalid-format"))
      || (!Array.isArray(value.definitions) && reject("definitions", "array-required"))
      || (value.definitions.length === 0 && reject("definitions", "array-empty"))
      || (value.definitions.length > 256 && reject("definitions", "definitions-too-many"))
      || (Object.getPrototypeOf(value.definitions) !== Array.prototype && reject("definitions", "plain-array-required"))
      || (Reflect.ownKeys(value.definitions).length !== value.definitions.length + 1 && reject("definitions", "dense-array-required"))
      || (Array.from({ length: value.definitions.length }, (_, index) => Object.getOwnPropertyDescriptor(value.definitions, String(index)))
        .some((field) => field === undefined || !("value" in field) || !field.enumerable) && reject("definitions", "data-fields-required"))) return failure();
    phase = "definitions";
    if (value.definitions.some((definition) => (!validDiagnosticDefinition(definition) && reject("definitions", "definition-invalid"))
      || (!definition.code.startsWith(`${value.owner}.`) && reject("definitions", "ownership-mismatch")))) return failure();
    phase = "conflicts";
    const identities = value.definitions.map((definition) => `${definition.code}@${definition.version}`);
    if ((new Set(identities).size !== identities.length && reject("identity", "duplicate-identity"))
      || existing.some((catalog) => (catalog.owner === value.owner && reject("owner", "duplicate-owner"))
        || (catalog.definitions.some((definition) => identities.includes(`${definition.code}@${definition.version}`)) && reject("identity", "duplicate-identity")))) return failure();
    phase = "snapshot";
    const snapshot = JSON.parse(JSON.stringify(value)) as PlatformDiagnosticCatalog;
    return { ok: true, value: snapshot };
  } catch { field = "declaration"; condition = "inspection-threw"; return failure(); }
}

function invalid(): Result<never, PlatformContractError> {
  return { ok: false, error: { code: "PLATFORM_CONTRACT_MALFORMED_DIAGNOSTIC_CATALOG", defaultMessage: "Diagnostic catalog is malformed, conflicts with registration or violates its ownership boundary." } };
}
