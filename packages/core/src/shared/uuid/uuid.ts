import { brand } from "../contract/branding";
import { err, ok, type Result } from "../contract/results";
import { coreUuidRecord } from "../diagnostics/records";
import type { UUID } from "./contracts";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** Validate and normalise an RFC 4122 UUID without retaining the supplied value in diagnostic evidence. */
export function uuid(value: string): Result<UUID> {
  if (!uuidPattern.test(value)) {
    return err({
      code: "INVALID_UUID",
      defaultMessage: "Expected a valid UUID string.",
      diagnosticRecord: coreUuidRecord("invalid-format"),
    });
  }
  return ok(brand<string, "UUID">(value.toLowerCase()));
}
