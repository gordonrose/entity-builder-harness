import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";
import { persistenceLeaseDurationReasons, type PersistenceLeaseDurationReason } from "../requirements";

export const persistenceRelayConfigurationDiagnostic = defineDiagnostic({
  code: "persistence.relay-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["configure-relay"] }, phase: { type: "enum", values: ["configuration"] },
    setting: { type: "enum", values: ["lease-duration"] }, reason: { type: "enum", values: persistenceLeaseDurationReasons },
    effect: { type: "enum", values: ["relay-not-created"] },
  } },
} as const);
export const persistenceLeasingDiagnosticCatalog = Object.freeze({ owner: "persistence", definitions: Object.freeze([persistenceRelayConfigurationDiagnostic]) });
export function persistenceRelayConfigurationRecord(reason: PersistenceLeaseDurationReason) {
  const checked = createDiagnosticRecord(persistenceRelayConfigurationDiagnostic, {
    operation: "configure-relay", phase: "configuration", setting: "lease-duration", reason, effect: "relay-not-created",
  });
  if (!checked.ok) throw new TypeError("PLATFORM_PERSISTENCE_RELAY_DIAGNOSTIC_INVALID");
  return checked.value;
}
