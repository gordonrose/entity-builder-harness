import { err } from "../contract/results";
import { coreUuidGenerationRecord } from "../diagnostics/records";
import type { UuidGenerator } from "./contracts";
import { uuid } from "./uuid";

/** The portable system implementation uses the Web Crypto UUID capability provided by supported runtimes. */
export const systemUuidGenerator: UuidGenerator = {
  generate() {
    try {
      const generated = uuid(globalThis.crypto.randomUUID());
      if (generated.ok) return generated;
      return err({
        code: "UUID_GENERATION_FAILED",
        defaultMessage: "The system could not generate a UUID.",
        diagnosticRecord: coreUuidGenerationRecord("generated-value-invalid"),
        relatedDiagnosticRecords: generated.error.diagnosticRecord === undefined ? [] : [generated.error.diagnosticRecord],
      });
    } catch (cause) {
      return err({
        code: "UUID_GENERATION_FAILED",
        defaultMessage: "The system could not generate a UUID.",
        cause,
        diagnosticRecord: coreUuidGenerationRecord("generation-threw"),
      });
    }
  },
};
