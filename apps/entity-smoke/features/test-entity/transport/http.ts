import { entityId, uuid } from "@kanbien/core/shared";
import type { PlatformResponse } from "@kanbien/platform-contracts";
import { createTestEntitySchema, updateTestEntitySchema } from "../contract/schemas";
import { testEntityValidationRecord } from "../contract/diagnostics";
import type { TestEntityError } from "../contract/errors";
import { deliverDiagnosticRecords, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { TestEntityServiceDependencies } from "../domain/services/dependencies";
import { createTestEntityService } from "../domain/services/create-test-entity";
import { getTestEntityService } from "../domain/services/get-test-entity";
import { listTestEntitiesService } from "../domain/services/list-test-entities";
import { updateTestEntityService } from "../domain/services/update-test-entity";
import { archiveTestEntityService } from "../domain/services/archive-test-entity";
import { restoreTestEntityService } from "../domain/services/restore-test-entity";
import { deleteTestEntityService } from "../domain/services/delete-test-entity";
import { restoreLogicallyDeletedTestEntityService } from "../domain/services/restore-logically-deleted-test-entity";
import { assessTestEntityPurgeEligibilityService } from "../domain/services/assess-test-entity-purge-eligibility";

/** Private smoke transport. It adapts commands; lifecycle stays in services.
 * No route executes hard purge or accepts a caller-selected clock/policy. */
export async function handleTestEntityCommand(body: unknown, deps: TestEntityServiceDependencies, onDiagnostic?: (record: DiagnosticRecord) => unknown): Promise<PlatformResponse> {
  const respond = (result: Parameters<typeof response>[0], success = 200) => response(result, success, onDiagnostic);
  if (typeof body !== "object" || body === null || Array.isArray(body)) return invalid();
  const command = body as Record<string, unknown>;
  if (command.action === "create") {
    if (!createTestEntitySchema.validate(command.input)) return invalid(createTestEntitySchema.diagnose?.(command.input));
    return respond(await createTestEntityService(command.input, deps), 201);
  }
  if (command.action === "list") {
    const input = { status: command.status };
    if (!updateTestEntitySchema.validate(input)) return invalid(updateTestEntitySchema.diagnose?.(input));
    return { status: 200, body: await listTestEntitiesService(input.status!, deps) };
  }
  if (typeof command.id !== "string" || !uuid(command.id).ok) return invalid();
  const id = entityId<"TestEntity">(command.id);
  switch (command.action) {
    case "get": {
      const entity = await getTestEntityService(id, deps);
      return entity === null ? { status: 404, body: { error: { code: "TEST_ENTITY_NOT_FOUND" } } } : { status: 200, body: entity };
    }
    case "update":
      if (!updateTestEntitySchema.validate(command.input)) return invalid(updateTestEntitySchema.diagnose?.(command.input));
      return respond(await updateTestEntityService(id, command.input, deps));
    case "archive": return respond(await archiveTestEntityService(id, deps));
    case "restore-archive": return respond(await restoreTestEntityService(id, deps));
    case "delete": return respond(await deleteTestEntityService(id, deps));
    case "restore-deleted": return respond(await restoreLogicallyDeletedTestEntityService(id, deps));
    case "assess-purge": {
      if (typeof command.retentionSatisfied !== "boolean" || typeof command.legalHold !== "boolean") return invalid();
      const eligibility = await assessTestEntityPurgeEligibilityService(id, { asOf: deps.clock.now(), retentionSatisfied: command.retentionSatisfied, legalHold: command.legalHold }, deps);
      return typeof eligibility === "string" ? { status: 200, body: { eligibility } } : respond({ ok: false, error: eligibility });
    }
    default: return invalid();
  }
}

function response(result: { readonly ok: true; readonly value: unknown } | { readonly ok: false; readonly error: TestEntityError }, success = 200, onDiagnostic?: (record: DiagnosticRecord) => unknown): PlatformResponse {
  if (result.ok) return { status: success, body: result.value };
  const error = result.error;
  // The response carries the primary; deliver companions through the selected
  // request reporter. Optional reporting cannot retry or change the result.
  try { if (onDiagnostic !== undefined) deliverDiagnosticRecords(error.relatedDiagnosticRecords ?? [], onDiagnostic); } catch { /* Keep the selected response. */ }
  return { status: errorStatus(error.code),
    body: { error: { code: error.code, message: error.defaultMessage } },
    observability: { errorClass: "test_entity_operation_failed", ...(error.diagnosticRecord === undefined ? {} : { diagnosticRecord: error.diagnosticRecord }) } };
}

function errorStatus(code: string): number {
  if (code === "TEST_ENTITY_NOT_FOUND") return 404;
  if (code === "TEST_ENTITY_ID_CONFLICT") return 409;
  if (code === "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED") return 503;
  return ["TEST_ENTITY_VALIDATION_FAILED", "TEST_ENTITY_DELETED", "TEST_ENTITY_ALREADY_ARCHIVED", "TEST_ENTITY_NOT_ARCHIVED",
    "PERSISTENCE_RECORD_NOT_DELETED", "PERSISTENCE_RESTORE_WINDOW_EXPIRED", "PERSISTENCE_INVALID_RECORD_LIFECYCLE"].includes(code) ? 400 : 500;
}

function invalid(record = testEntityValidationRecord("input", "invalid-value")): PlatformResponse {
  return { status: 400, body: { error: { code: "TEST_ENTITY_INVALID_INPUT" } }, observability: { errorClass: "test_entity_request_invalid", diagnosticRecord: record } };
}
