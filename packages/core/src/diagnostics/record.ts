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

export interface DiagnosticEvidence {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}
export type DiagnosticSelectionStatus = "absent" | "selected" | "rejected" | "unselected" | "inaccessible";
export interface DiagnosticEvidenceInspection {
  readonly evidence: DiagnosticEvidence;
  readonly primary: DiagnosticSelectionStatus;
  readonly companions: {
    readonly status: Exclude<DiagnosticSelectionStatus, "unselected">;
    readonly entries: readonly DiagnosticSelectionStatus[];
  };
}

/** Compatibility projection. Use inspection when absence and rejection matter. */
export function selectDiagnosticEvidence(definitions: readonly DiagnosticDefinition[], value: unknown): DiagnosticEvidence {
  return inspectDiagnosticEvidence(definitions, value).evidence;
}

/** Only bounded outcomes leave this boundary, never rejected values or exception text. */
export function inspectDiagnosticEvidence(definitions: readonly DiagnosticDefinition[], value: unknown): DiagnosticEvidenceInspection {
  const primaryField = ownDataField(value, "diagnosticRecord");
  const primary = primaryField.status === "present"
    ? inspectRecord(definitions, primaryField.value)
    : { status: primaryField.status };
  // Read independently: a malformed primary or a throwing proxy trap must not
  // discard companions that can be validated at this boundary.
  const companions = inspectRelatedRecords(definitions, ownDataField(value, "relatedDiagnosticRecords"));
  return Object.freeze({
    evidence: Object.freeze({
      ...("record" in primary && primary.record !== undefined ? { diagnosticRecord: primary.record } : {}),
      ...(companions.records === undefined ? {} : { relatedDiagnosticRecords: companions.records }),
    }),
    primary: primary.status,
    companions: Object.freeze({ status: companions.status, entries: Object.freeze(companions.entries) }),
  });
}

type DataField = { readonly status: "present"; readonly value: unknown } | { readonly status: "absent" | "inaccessible" };
function ownDataField(value: unknown, key: string): DataField {
  try {
    if ((typeof value !== "object" || value === null) && typeof value !== "function") return { status: "absent" };
    const field = Object.getOwnPropertyDescriptor(value, key);
    if (field === undefined) return { status: "absent" };
    if (!("value" in field)) return { status: "inaccessible" };
    return field.value === undefined ? { status: "absent" } : { status: "present", value: field.value };
  } catch { return { status: "inaccessible" }; }
}

function inspectRecord(definitions: readonly DiagnosticDefinition[], value: unknown): {
  readonly status: Exclude<DiagnosticSelectionStatus, "absent">; readonly record?: DiagnosticRecord;
} {
  try {
    const code = ownDataField(value, "code");
    const version = ownDataField(value, "definitionVersion");
    if (code.status === "inaccessible" || version.status === "inaccessible") return { status: "inaccessible" };
    if (code.status !== "present" || typeof code.value !== "string" || version.status !== "present"
      || !Number.isSafeInteger(version.value) || (version.value as number) < 1) return { status: "rejected" };
    const definition = definitions.find((candidate) => candidate.code === code.value && candidate.version === version.value);
    if (definition === undefined) return { status: "unselected" };
    const checked = parseDiagnosticRecord(definition, value);
    return checked.ok ? { status: "selected", record: checked.value } : { status: "rejected" };
  } catch { return { status: "inaccessible" }; }
}

function inspectRelatedRecords(definitions: readonly DiagnosticDefinition[], field: DataField): {
  readonly status: Exclude<DiagnosticSelectionStatus, "unselected">;
  readonly entries: DiagnosticSelectionStatus[];
  readonly records?: readonly DiagnosticRecord[];
} {
  if (field.status !== "present") return { status: field.status, entries: [] };
  const value = field.value;
  try {
    if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) return { status: "rejected", entries: [] };
    const length = Object.getOwnPropertyDescriptor(value, "length");
    if (length === undefined || !("value" in length) || !Number.isSafeInteger(length.value)
      || length.value < 0 || length.value > diagnosticRelatedRecordLimit
      || Reflect.ownKeys(value).length !== length.value + 1) return { status: "rejected", entries: [] };
    const entries: unknown[] = [];
    for (let index = 0; index < length.value; index++) {
      const field = Object.getOwnPropertyDescriptor(value, String(index));
      if (field === undefined || !("value" in field) || field.enumerable !== true) return { status: "rejected", entries: [] };
      entries.push(field.value);
    }
    // List integrity is established before any entry is examined. Unselected or
    // malformed records are excluded independently, retaining observation order.
    const copied: DiagnosticRecord[] = [];
    const outcomes: DiagnosticSelectionStatus[] = [];
    for (const entry of entries) {
      const checked = inspectRecord(definitions, entry);
      outcomes.push(checked.status);
      if (checked.record !== undefined) copied.push(checked.record);
    }
    return { status: "selected", entries: outcomes, records: Object.freeze(copied) };
  } catch { return { status: "inaccessible", entries: [] }; }
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
