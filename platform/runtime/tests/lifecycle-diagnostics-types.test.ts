import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformDiagnosticCatalog, PlatformDiagnosticContext } from "@kanbien/platform-contracts";
import { createPlatformRuntimeLifecycle, type PlatformRuntimeDiagnosticOptions, type PlatformRuntimeError } from "../src/index";
const legacy: PlatformRuntimeError = { code: "PLATFORM_RUNTIME_LIFECYCLE_FAILED", defaultMessage: "Legacy" };
const options: PlatformRuntimeDiagnosticOptions = { diagnosticDefinitions: [], onDiagnostic(record: DiagnosticRecord, context: PlatformDiagnosticContext, catalogs?: readonly PlatformDiagnosticCatalog[]) { void record; void context; void catalogs; } };
void createPlatformRuntimeLifecycle({ apps: [], ...options }); void legacy;
// @ts-expect-error Diagnostic callbacks receive a data-only record, not an arbitrary message string.
const invalid: PlatformRuntimeDiagnosticOptions = { onDiagnostic: (record: string) => record };
void invalid;
