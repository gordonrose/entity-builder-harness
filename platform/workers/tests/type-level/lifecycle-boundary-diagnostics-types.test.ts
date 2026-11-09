import type { PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import type { PlatformWorkerError, PlatformWorkerProcessOptions, PlatformWorkerShellOptions } from "../../src/index";
const catalogs: readonly PlatformDiagnosticCatalog[] = [];
const processOptions: PlatformWorkerProcessOptions = { diagnosticCatalogs: catalogs };
const shellOptions: Pick<PlatformWorkerShellOptions, "diagnosticCatalogs"> = { diagnosticCatalogs: catalogs };
const legacy: PlatformWorkerError = { code: "PLATFORM_WORKER_HANDLER_FAILED", defaultMessage: "Legacy" };
void processOptions; void shellOptions; void legacy;
// @ts-expect-error Catalog selection requires actual typed catalogs, not arbitrary strings.
const invalid: PlatformWorkerProcessOptions = { diagnosticCatalogs: ["private"] };
void invalid;
