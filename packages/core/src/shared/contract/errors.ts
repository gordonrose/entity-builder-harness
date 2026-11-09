import type { DiagnosticDescriptor, DiagnosticRecord } from "../../diagnostics/index";
import type { MessageDescriptor } from "./messages";

export interface CoreError extends MessageDescriptor {
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  /** Validated detail is separate from legacy primitive diagnostic facts. */
  readonly diagnosticRecord?: DiagnosticRecord;
  /** Bounded, independently schema-validated observations; never raw causes. */
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly details?: Readonly<Record<string, unknown>>;
}
