import type { LogRecord } from "@kanbien/core/logging";

// Package-private provenance, not a structural flag that raw log input can spoof.
// Only the reporter imports the constructor after catalog parsing. The record
// and its fields are frozen; its diagnostic tree already has the core budgets.
const validatedLogs = new WeakSet<LogRecord>();

export function validatedDiagnosticLog(record: LogRecord): LogRecord {
  if (record.fields !== undefined) Object.freeze(record.fields);
  Object.freeze(record);
  validatedLogs.add(record);
  return record;
}

export function hasValidatedDiagnosticLogOrigin(record: LogRecord): boolean {
  return validatedLogs.has(record);
}
