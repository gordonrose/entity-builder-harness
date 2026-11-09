import { coreDiagnosticCatalog, configError, type ConfigError, type DiagnosticRecord } from "../../../src/index";
import { coreConfigPrimitiveRecord, coreConfigSourceRecord, coreConfigDiagnosticDefinitions } from "../../../src/config/index";
import { coreJsonRecord, coreDateRecord, coreSharedDiagnosticDefinitions } from "../../../src/shared/index";
import { coreSecurityPrimitiveRecord, coreSecurityDiagnosticDefinitions } from "../../../src/security/index";
import { corePermissionRecord, coreAuthzDiagnosticDefinitions } from "../../../src/authz/index";
import { coreAuditDiagnosticDefinitions, coreEventDiagnosticDefinitions, coreFileDiagnosticDefinitions, coreI18nDiagnosticDefinitions, coreLocalizationDiagnosticDefinitions } from "../../../src/index";

const primitive = coreConfigPrimitiveRecord({ field: "value", reader: "number", reason: "non-finite" });
const historical: ConfigError = { code: "CONFIG_MISSING", issues: [{ path: [], code: "CUSTOM", defaultMessage: "Required." }] };
const enriched: ConfigError = configError(historical.code, historical.issues, { diagnosticRecord: primitive, relatedDiagnosticRecords: [primitive] });
const evidence: DiagnosticRecord | undefined = enriched.diagnosticRecord;
const related: readonly DiagnosticRecord[] | undefined = enriched.relatedDiagnosticRecords;
const catalog: { readonly owner: string; readonly definitions: readonly import("../../../src/diagnostics/index").DiagnosticDefinition[] } = coreDiagnosticCatalog;
void [evidence, related, catalog, coreConfigDiagnosticDefinitions, coreSharedDiagnosticDefinitions, coreSecurityDiagnosticDefinitions, coreAuthzDiagnosticDefinitions];
const capabilityDefinitions: readonly (readonly import("../../../src/diagnostics/index").DiagnosticDefinition[])[] =
  [coreAuditDiagnosticDefinitions, coreEventDiagnosticDefinitions, coreFileDiagnosticDefinitions, coreI18nDiagnosticDefinitions, coreLocalizationDiagnosticDefinitions];
void capabilityDefinitions;
coreConfigSourceRecord("schema", 0);
coreJsonRecord("non-plain-object", 1, [0]);
coreDateRecord("parse-rejected");
coreSecurityPrimitiveRecord("hash-value", "whitespace");
corePermissionRecord("action", "colon-separator");
// @ts-expect-error Arbitrary source keys are not approved diagnostic readers.
coreConfigSourceRecord("PRIVATE_SOURCE_KEY");
// @ts-expect-error Raw values do not belong in a primitive diagnostic.
coreConfigPrimitiveRecord({ field: "value", reader: "string", reason: "wrong-type", value: "private" });
// @ts-expect-error A raw field label is not an approved security field.
coreSecurityPrimitiveRecord("raw-secret", "empty");
// @ts-expect-error Permission diagnostic reasons use the closed guard vocabulary.
corePermissionRecord("resource", "raw-error-message");
// @ts-expect-error Related observations must be records, not native errors.
configError(historical.code, historical.issues, { relatedDiagnosticRecords: [new Error("private")] });
