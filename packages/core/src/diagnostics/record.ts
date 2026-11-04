import type { Result } from "../shared/index";
import { validDiagnosticDefinition, type DiagnosticDefinition } from "./definition";
import { copyDiagnosticDetail, diagnosticObject } from "./schema";

export interface DiagnosticRecord<TDetail = unknown> {
  readonly schema: "core/diagnostic-record/v1";
  readonly code: string;
  readonly definitionVersion: number;
  readonly detail: TDetail;
}
export interface DiagnosticRecordError { readonly code: "DIAGNOSTIC_RECORD_INVALID" }
/** Shared envelope bound; catalogs export this value for non-TypeScript readers. */
export const diagnosticRelatedRecordLimit = 8;

/** Select only owned data evidence; never traverse an exception's cause or prototype. */
export function selectDiagnosticEvidence(definitions: readonly DiagnosticDefinition[], value: unknown): {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
} {
  const primary = selectedRecord(definitions, ownDataValue(value, "diagnosticRecord"));
  // Read independently: a malformed primary or a throwing proxy trap must not
  // discard companions that can be validated at this boundary.
  const companions = selectedRelatedRecords(definitions, ownDataValue(value, "relatedDiagnosticRecords"));
  return Object.freeze({
    ...(primary === undefined ? {} : { diagnosticRecord: primary }),
    ...(companions === undefined ? {} : { relatedDiagnosticRecords: companions }),
  });
}

function ownDataValue(value: unknown, key: string): unknown {
  try {
    if ((typeof value !== "object" || value === null) && typeof value !== "function") return undefined;
    const field = Object.getOwnPropertyDescriptor(value, key);
    return field !== undefined && "value" in field ? field.value : undefined;
  } catch { return undefined; }
}

function selectedRecord(definitions: readonly DiagnosticDefinition[], value: unknown): DiagnosticRecord | undefined {
  try {
    const code = ownDataValue(value, "code");
    const version = ownDataValue(value, "definitionVersion");
    const definition = definitions.find((candidate) => candidate.code === code && candidate.version === version);
    if (definition === undefined) return undefined;
    const checked = parseDiagnosticRecord(definition, value);
    return checked.ok ? checked.value : undefined;
  } catch { return undefined; }
}

function selectedRelatedRecords(definitions: readonly DiagnosticDefinition[], value: unknown): readonly DiagnosticRecord[] | undefined {
  try {
    if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) return undefined;
    const length = Object.getOwnPropertyDescriptor(value, "length");
    if (length === undefined || !("value" in length) || !Number.isSafeInteger(length.value)
      || length.value < 0 || length.value > diagnosticRelatedRecordLimit
      || Reflect.ownKeys(value).length !== length.value + 1) return undefined;
    const entries: unknown[] = [];
    for (let index = 0; index < length.value; index++) {
      const field = Object.getOwnPropertyDescriptor(value, String(index));
      if (field === undefined || !("value" in field) || field.enumerable !== true) return undefined;
      entries.push(field.value);
    }
    // List integrity is established before any entry is examined. Unselected or
    // malformed records are excluded independently, retaining observation order.
    const copied: DiagnosticRecord[] = [];
    for (const entry of entries) {
      const checked = selectedRecord(definitions, entry);
      if (checked !== undefined) copied.push(checked);
    }
    return Object.freeze(copied);
  } catch { return undefined; }
}

/** Copies a dense, data-only bounded list and validates every registered record. */
export function parseRelatedDiagnosticRecords(definitions: readonly DiagnosticDefinition[], value: unknown): Result<readonly DiagnosticRecord[], DiagnosticRecordError> {
  try {
    if (!Array.isArray(value) || value.length > diagnosticRelatedRecordLimit || Object.getPrototypeOf(value) !== Array.prototype
      || Reflect.ownKeys(value).length !== value.length + 1) return invalid();
    const copied: DiagnosticRecord[] = [];
    for (let index = 0; index < value.length; index++) {
      const field = Object.getOwnPropertyDescriptor(value, String(index));
      if (!field || !("value" in field) || !diagnosticObject(field.value)) return invalid();
      const definition = definitions.find((candidate) => candidate.code === field.value.code && candidate.version === field.value.definitionVersion);
      if (!definition) return invalid();
      const checked = parseDiagnosticRecord(definition, field.value);
      if (!checked.ok) return invalid();
      copied.push(checked.value);
    }
    return { ok: true, value: Object.freeze(copied) };
  } catch { return invalid(); }
}
const invalid = (): Result<never, DiagnosticRecordError> => ({ ok: false, error: { code: "DIAGNOSTIC_RECORD_INVALID" } });

export function createDiagnosticRecord<TDetail>(definition: DiagnosticDefinition<TDetail>, detail: NoInfer<TDetail>): Result<DiagnosticRecord<TDetail>, DiagnosticRecordError> {
  try {
    if (!validDiagnosticDefinition(definition)) return invalid();
    const copied = copyDiagnosticDetail(definition.detail, detail) as TDetail;
    const record = { schema: "core/diagnostic-record/v1" as const, code: definition.code, definitionVersion: definition.version, detail: copied };
    if (JSON.stringify(record).length > 16_384) return invalid();
    return { ok: true, value: Object.freeze(record) };
  } catch { return invalid(); }
}

export function parseDiagnosticRecord<TDetail>(definition: DiagnosticDefinition<TDetail>, value: unknown): Result<DiagnosticRecord<TDetail>, DiagnosticRecordError> {
  try {
    if (!diagnosticObject(value) || Object.keys(value).sort().join(",") !== "code,definitionVersion,detail,schema"
      || value["schema"] !== "core/diagnostic-record/v1" || value["code"] !== definition.code
      || value["definitionVersion"] !== definition.version) return invalid();
    return createDiagnosticRecord(definition, value["detail"] as TDetail);
  } catch { return invalid(); }
}
