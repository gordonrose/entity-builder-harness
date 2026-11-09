import { coreConfigDiagnosticCatalog } from "./config/contract/reporting/diagnostics";
import { diagnosticProcessingDefinition } from "./diagnostics/reporting/processing";
import { coreSharedDiagnosticDefinitions } from "./shared/index";
import { coreSecurityDiagnosticDefinitions } from "./security/diagnostics";
import { coreAuthzDiagnosticDefinitions } from "./authz/diagnostics";
import { coreAuthnDiagnosticDefinitions } from "./authn/diagnostics";
import { coreTenancyDiagnosticDefinitions } from "./tenancy/diagnostics";
import { corePersistenceDiagnosticDefinitions } from "./persistence/diagnostics";
import { coreQueueDiagnosticDefinitions } from "./queues/diagnostics";
import { coreMonitoringDiagnosticDefinitions } from "./monitoring/boundary-diagnostics";
import { coreLoggingDiagnosticDefinitions } from "./logging/diagnostics";
import { coreAuditDiagnosticDefinitions } from "./audit/diagnostics";
import { coreEventDiagnosticDefinitions } from "./events/diagnostics";
import { coreFileDiagnosticDefinitions } from "./files/diagnostics";
import { coreI18nDiagnosticDefinitions } from "./i18n/diagnostics";
import { coreLocalizationDiagnosticDefinitions } from "./localization/diagnostics";

/** Explicitly selected by consumers; the diagnostics framework stays capability-free. */
export const coreDiagnosticCatalog = Object.freeze({ owner: "core", definitions: Object.freeze([
  ...coreConfigDiagnosticCatalog.definitions, ...coreSharedDiagnosticDefinitions,
  ...coreSecurityDiagnosticDefinitions, ...coreAuthzDiagnosticDefinitions,
  ...coreAuthnDiagnosticDefinitions, ...coreTenancyDiagnosticDefinitions,
  ...corePersistenceDiagnosticDefinitions,
  ...coreQueueDiagnosticDefinitions,
  ...coreMonitoringDiagnosticDefinitions, ...coreLoggingDiagnosticDefinitions,
  ...coreAuditDiagnosticDefinitions, ...coreEventDiagnosticDefinitions, ...coreFileDiagnosticDefinitions,
  ...coreI18nDiagnosticDefinitions, ...coreLocalizationDiagnosticDefinitions,
  diagnosticProcessingDefinition(),
]) });
