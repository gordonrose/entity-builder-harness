import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { serverClientAddressFallbackRecord, serverConfigurationOmissionRecord, serverProcessBoundaryRecord,
  serverRequestBoundaryRecord, serverRequestPredicateRecord, serverTransportRejectionRecord } from "../../src/diagnostics";
import type { PlatformClientAddressResolverInput, PlatformServerTransportFailure } from "../../src/transport";

const record: DiagnosticRecord = serverClientAddressFallbackRecord("forwarded-header-missing", "socket-peer");
const input: PlatformClientAddressResolverInput = { headers: {}, onDiagnostic: (selected) => { void selected; } };
void input;
const transportEvidence: Pick<PlatformServerTransportFailure, "diagnosticRecord" | "relatedDiagnosticRecords"> = {
  diagnosticRecord: record, relatedDiagnosticRecords: [record],
};
void transportEvidence;
serverConfigurationOmissionRecord("release.source-commit", "format-rejected");
serverProcessBoundaryRecord("shutdown-close", "shutdown-not-completed");
serverRequestPredicateRecord("tenantId", "string-required", "tenant-resolution");
serverRequestBoundaryRecord("route-parameter-decoding", "handler-not-invoked", 0);
serverTransportRejectionRecord("handler-deadline-observed", "handler", "handler-still-pending");
// @ts-expect-error diagnostic reasons are not arbitrary provider or request text.
serverClientAddressFallbackRecord("raw-private-value", "socket-peer");
// @ts-expect-error no actual addresses belong in diagnostic source fields.
serverClientAddressFallbackRecord("forwarded-header-missing", "127.0.0.1");
// @ts-expect-error request locations are closed logical fields, not supplied tenant identities.
serverRequestPredicateRecord("raw-tenant", "string-required", "tenant-resolution");
// @ts-expect-error boundary phases do not accept arbitrary exception strings.
serverRequestBoundaryRecord("raw-error", "handler-not-invoked");
// @ts-expect-error telemetry details cannot change legacy public HTTP failure status typing.
const invalidStatus: Pick<PlatformServerTransportFailure, "status"> = { status: "failed" };
void invalidStatus;
