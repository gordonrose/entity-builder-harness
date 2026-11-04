import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformConfigurationLoadingDiagnostic } from "./diagnostics";

type Detail = NonNullable<typeof platformConfigurationLoadingDiagnostic.__detail>;
export function rejectPlatformConfigurationDeclaration(field: Detail["field"], reason: Detail["reason"]): never {
  const checked = createDiagnosticRecord(platformConfigurationLoadingDiagnostic, { field, reason, effect: "not-started" });
  const error = new TypeError("PLATFORM_CONFIGURATION_LOADING_DECLARATION_INVALID");
  throw checked.ok ? Object.assign(error, { diagnosticRecord: checked.value }) : error;
}
