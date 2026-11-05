import { diagnosticDescriptor, type DiagnosticDescriptor } from "./index";
import { diagnosticObject, validDiagnosticSchema, type DiagnosticDetail, type DiagnosticDetailSchema } from "./schema";

export type DiagnosticClassification = Omit<DiagnosticDescriptor, "facts" | "messageKey">;
export interface DiagnosticDefinition<TDetail = unknown> {
  readonly code: string;
  readonly version: number;
  readonly classification: DiagnosticClassification;
  readonly detail: DiagnosticDetailSchema;
  /** Compile-time detail inference; never included in the serialized contract. */
  readonly __detail?: TDetail;
}

export function validDiagnosticDefinition(value: unknown): value is DiagnosticDefinition {
  try {
    if (!diagnosticObject(value) || Object.keys(value).sort().join(",") !== "classification,code,detail,version"
      || typeof value["code"] !== "string" || !/^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/.test(value["code"])
      || value["code"].length > 128 || !Number.isSafeInteger(value["version"]) || (value["version"] as number) < 1
      || !diagnosticObject(value["classification"]) || !validDiagnosticSchema(value["detail"])) return false;
    const classification = value["classification"];
    if (Object.keys(classification).some((key) => !["failureKind", "failureSource", "severity", "recovery", "retryable", "userCorrectable", "action"].includes(key))
      || typeof classification["retryable"] !== "boolean" || typeof classification["userCorrectable"] !== "boolean") return false;
    diagnosticDescriptor(classification as unknown as DiagnosticClassification);
    return true;
  } catch { return false; }
}

export function defineDiagnostic<const S extends DiagnosticDetailSchema>(input: {
  readonly code: string;
  readonly version: number;
  readonly classification: Omit<DiagnosticClassification, "retryable" | "userCorrectable"> & { readonly retryable?: boolean; readonly userCorrectable?: boolean };
  readonly detail: S;
}): DiagnosticDefinition<DiagnosticDetail<S>> {
  const definition = { code: input.code, version: input.version, classification: diagnosticDescriptor(input.classification), detail: input.detail };
  if (!validDiagnosticDefinition(definition)) throw new TypeError("DIAGNOSTIC_DEFINITION_INVALID");
  // Snapshot reviewed plain data, not functions or references to caller state.
  return freezeDefinition(JSON.parse(JSON.stringify(definition))) as DiagnosticDefinition<DiagnosticDetail<S>>;
}

function freezeDefinition(value: unknown): unknown {
  if (typeof value === "object" && value !== null) {
    for (const child of Object.values(value)) freezeDefinition(child);
    Object.freeze(value);
  }
  return value;
}
