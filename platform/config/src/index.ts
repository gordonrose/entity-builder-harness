export { defineConfigurationDiagnostic, configurationDiagnostic, platformConfigDiagnostic, platformConfigDiagnosticCatalog, defineConfigurationSourceReadDiagnostic, configurationSourceReadDiagnosticRecord, defineConfigurationRelationshipDiagnostics, configurationRelationshipDiagnostic } from "./diagnostics";
export type { PlatformConfigErrorCode, PlatformConfigError, PlatformConfigValidationInput } from "./contract/validation";
export { validatePlatformConfigSchemas, assertPlatformConfigValid } from "./domain/validation";
export type { PlatformConfigurationLoadingInput, PlatformConfigurationLoadingResult } from "./contract/loading";
export { loadPlatformConfiguration } from "./domain/loading";
