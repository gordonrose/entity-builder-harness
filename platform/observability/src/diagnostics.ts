import { parseDiagnosticRecord, diagnosticRelatedRecordLimit, deliverDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Logger } from "@kanbien/core/logging";
import type { Clock } from "@kanbien/core/shared";
import { validatedDiagnosticLog } from "./diagnostic-log";
import { platformDiagnosticContext, validatePlatformDiagnosticCatalog, type PlatformDiagnosticCatalog, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";

const intrinsicPromiseThen = Promise.prototype.then;

/** True means asynchronous/unconfirmed; ordinary nonthenable void-port returns remain accepted. */
export function observePlatformSinkCompletion(value: unknown, rejected: (error: unknown) => void): boolean {
  if ((typeof value !== "object" || value === null) && typeof value !== "function") return false;
  const fail = (error: unknown): void => { try { rejected(error); } catch { /* Never orphan a rejection. */ } };
  try { Reflect.apply(intrinsicPromiseThen, value, [undefined, fail]); return true; }
  catch { /* Non-native values require ordinary thenable selection. */ }
  let then: unknown;
  try { then = (value as { then?: unknown }).then; }
  catch (error) { fail(error); return true; }
  if (typeof then !== "function") return false;
  try {
    const assimilated = Promise.resolve({ then(resolve: (value: unknown) => void, reject: (reason: unknown) => void) { return Reflect.apply(then, value, [resolve, reject]); } });
    Reflect.apply(intrinsicPromiseThen, assimilated, [undefined, fail]);
  } catch (error) { fail(error); }
  return true;
}

/** Optional delivery never waits, replays work or leaks reporter exceptions. */
export function reportPlatformDiagnostic(reporter: PlatformDiagnosticReporter, record: DiagnosticRecord, context: PlatformDiagnosticContext): void {
  deliverDiagnosticRecord(record, selected => reporter.report(selected, context));
}

/** Available before app mount and for one-shot programs. No provider selection. */
export function createPlatformDiagnosticReporter(options: { readonly catalogs: readonly PlatformDiagnosticCatalog[]; readonly logger: Logger; readonly clock: Clock }): PlatformDiagnosticReporter {
  const catalogs: PlatformDiagnosticCatalog[] = [];
  for (const catalog of options.catalogs) {
    const checked = validatePlatformDiagnosticCatalog(catalog, catalogs);
    if (!checked.ok) throw Object.assign(new TypeError("PLATFORM_DIAGNOSTIC_CATALOG_INVALID"), {
      ...(checked.error.diagnosticRecord === undefined ? {} : { diagnosticRecord: checked.error.diagnosticRecord }),
    });
    catalogs.push(checked.value);
  }
  const definitions = catalogs.flatMap((catalog) => catalog.definitions);
  return {
    report(record, context) {
      try {
        const code = Object.getOwnPropertyDescriptor(record, "code");
        const version = Object.getOwnPropertyDescriptor(record, "definitionVersion");
        if (!code || !("value" in code) || !version || !("value" in version)) return { status: "rejected" };
        const definition = definitions.find((item) => item.code === code.value && item.version === version.value);
        if (!definition) return { status: "rejected" };
        const checked = parseDiagnosticRecord(definition, record);
        const selectedContext = platformDiagnosticContext(context);
        if (!checked.ok || !selectedContext) return { status: "rejected" };
        context = selectedContext;
        try {
          const pending: unknown = options.logger.write(validatedDiagnosticLog({ level: definition.classification.severity === "warning" ? "warn" : definition.classification.severity === "info" ? "info" : "error",
          message: "platform.diagnostic.observed",
          ...(context.correlationId === undefined ? {} : { correlationId: context.correlationId }), fields: {
            diagnostic: checked.value, capability: context.capability, operation: context.operation,
            stage: context.stage, observed_at: options.clock.now().toISOString(),
          } }));
          return { status: observePlatformSinkCompletion(pending, () => undefined) ? "unavailable" : "written" };
        } catch { return { status: "unavailable" }; }
      } catch { return { status: "rejected" }; }
    },
  };
}

/** Never enumerate an exception or read an accessor to obtain diagnostic data. */
export function reportPlatformErrorDiagnostic(reporter: PlatformDiagnosticReporter, error: unknown, context: Parameters<PlatformDiagnosticReporter["report"]>[1]): void {
  try {
    if (typeof error !== "object" || error === null) return;
    const field = Object.getOwnPropertyDescriptor(error, "diagnosticRecord");
    if (field && "value" in field && field.value !== undefined) {
      reportPlatformDiagnostic(reporter, field.value as DiagnosticRecord, context);
    }
    const related = Object.getOwnPropertyDescriptor(error, "relatedDiagnosticRecords");
    if (!related || !("value" in related)) return;
    const records: unknown = related.value;
    if (!Array.isArray(records) || Object.getPrototypeOf(records) !== Array.prototype || records.length > diagnosticRelatedRecordLimit || Reflect.ownKeys(records).length !== records.length + 1) return;
    for (let index = 0; index < records.length; index++) {
      const item = Object.getOwnPropertyDescriptor(records, String(index));
      if (!item || !("value" in item)) return;
    }
    for (let index = 0; index < records.length; index++) {
      const item = Object.getOwnPropertyDescriptor(records, String(index))!;
      reportPlatformDiagnostic(reporter, item.value as DiagnosticRecord, context);
    }
  } catch { /* Diagnostics cannot change the operation's outcome or cause replay. */ }
}
