import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PersistenceLeaseDurationReason } from "../requirements";
import { persistenceRelayConfigurationRecord } from "./diagnostics";

export function persistenceRelayConfigurationError(reason: PersistenceLeaseDurationReason): TypeError & { readonly diagnosticRecord: DiagnosticRecord } {
  return Object.assign(new TypeError("Persistence relay lease duration is invalid."), { diagnosticRecord: persistenceRelayConfigurationRecord(reason) });
}
