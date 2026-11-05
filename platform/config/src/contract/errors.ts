import { captureDiagnosticRecord, createDiagnosticRecord, requireDiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformConfigurationLoadingDiagnostic } from "./diagnostics";

type Detail = NonNullable<typeof platformConfigurationLoadingDiagnostic.__detail>;
export function rejectPlatformConfigurationDeclaration(field: Detail["field"], reason: Detail["reason"]): never {
  const diagnosticRecord = requireDiagnosticRecord([platformConfigurationLoadingDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(platformConfigurationLoadingDiagnostic, { field, reason, effect: "not-started" });
    return checked.ok ? checked.value : undefined;
  }));
  const error = new TypeError("PLATFORM_CONFIGURATION_LOADING_DECLARATION_INVALID");
  throw Object.assign(error, { diagnosticRecord });
}
