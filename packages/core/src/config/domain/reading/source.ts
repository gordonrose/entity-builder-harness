import { attachCoreDiagnosticRecord } from "../../../shared/index";
import { captureDiagnosticRecord, requireDiagnosticRecord } from "../../../diagnostics/index";
import { coreConfigSourceDiagnostic, coreConfigSourceRecord, type CoreConfigReader } from "../../contract/reporting/diagnostics";
import type { ConfigRecord, ConfigSource, ConfigValue } from "../../contract/types";

export function recordConfigSource(values: ConfigRecord): ConfigSource {
  const snapshot = { ...values };

  return {
    get: (key) => snapshot[key],
  };
}

export function readConfigSource(source: ConfigSource, key: string, reader: CoreConfigReader): ConfigValue | undefined {
  try { return source.get(key); }
  catch (error) { throw attachCoreDiagnosticRecord(error, requireDiagnosticRecord([coreConfigSourceDiagnostic], captureDiagnosticRecord(() => coreConfigSourceRecord(reader)))); }
}
