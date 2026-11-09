import { brand } from "../contract/branding";
import { err, ok, type Result } from "../contract/results";
import { attachCoreDiagnosticRecord, coreDateRecord, coreDateNormalizationRecord } from "../diagnostics/records";
import type { ISODateTime } from "./contracts";

const isoDateTimePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

export function isoDateTime(value: string): Result<ISODateTime> {
  if (!isoDateTimePattern.test(value)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
      diagnosticRecord: coreDateRecord("invalid-format"),
    });
  }

  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
      diagnosticRecord: coreDateRecord("parse-rejected"),
    });
  }

  try { return ok(brand<string, "ISODateTime">(new Date(timestamp).toISOString())); }
  catch (error) { throw attachCoreDiagnosticRecord(error, coreDateNormalizationRecord("string-normalization")); }
}

export function isoDateTimeFromDate(value: Date): ISODateTime {
  try { return brand<string, "ISODateTime">(value.toISOString()); }
  catch (error) { throw attachCoreDiagnosticRecord(error, coreDateNormalizationRecord("date-normalization")); }
}
