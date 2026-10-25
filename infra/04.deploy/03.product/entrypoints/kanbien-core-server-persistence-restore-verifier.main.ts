// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-restore-verifier
//   version: 3
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Verify a declared synthetic acceptance record in an isolated restored PostgreSQL copy using only the runtime credential.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { createNodePostgreSqlTokenConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";

import { persistenceConfiguration, persistenceCertificateAuthority, environmentText as text } from "./kanbien-core-server-persistence-configuration";
import { persistenceIamAuthentication } from "./kanbien-core-server-persistence-iam-authentication";

/**
 * This is intentionally a direct database client only for an isolated restore
 * rehearsal. Its task identity and security group are restricted to the
 * restored database; the normal private verifier remains server-mediated.
 */
export async function runKanbienCoreServerPersistenceRestoreVerifier(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const configuration = persistenceConfiguration(env, "restore");
  const credentials = configuration === undefined ? undefined : persistenceIamAuthentication(env, configuration, "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME");
  const expected = expectedRecord(env);
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (configuration === undefined || credentials === undefined || expected === undefined || certificateAuthority === undefined) return rejected("PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID");
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  try {
    const result = await pool.query<{ readonly record_id: string; readonly fact_digest: string }>({
      text: `SELECT record_id, fact_digest FROM ${acceptanceTable(configuration.schema)} WHERE record_id = $1`,
      values: [expected.recordId],
    });
    const row = result.rows[0];
    if (row?.record_id === expected.recordId && row.fact_digest === expected.factDigest) return accepted("KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED");
    return rejected("KANBIEN_CORE_PERSISTENCE_RESTORE_RECORD_MISMATCH");
  } catch (error) {
    return rejected(restoreVerificationFailureCode(error));
  } finally {
    await pool.end();
  }
}

/**
 * This verifier deliberately emits a closed, non-secret diagnostic taxonomy.
 * PostgreSQL errors often include endpoint, role, SQL, or credential material;
 * none of that crosses the task's safe result boundary.  The categories are
 * enough for the governed controller to distinguish a retryable path outage
 * from a configuration/identity or restore-content correction.
 */
export function restoreVerificationFailureCode(error: unknown): string {
  // `pg`, Node TLS, and a small number of AWS client wrappers can retain the
  // useful machine code on a causal error.  Read only that closed field: never
  // turn a provider message, endpoint, query, or credential-bearing value into
  // a result code.
  const code = errorCode(error) ?? errorCode(errorCause(error));
  if (code === "28P01" || code === "28000") return "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED";
  if (code === "42501") return "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED";
  if (code === "3D000" || code === "42P01") return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE";
  if (code === "ECONNREFUSED" || code === "ECONNRESET" || code === "ETIMEDOUT" || code === "EHOSTUNREACH" || code === "ENETUNREACH" || code === "EAI_AGAIN" || code === "ENOTFOUND") return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE";
  if (code === "CERT_HAS_EXPIRED" || code === "ERR_TLS_CERT_ALTNAME_INVALID" || code === "SELF_SIGNED_CERT_IN_CHAIN" || code === "UNABLE_TO_VERIFY_LEAF_SIGNATURE") return "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID";
  return "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE";
}

function errorCode(error: unknown): string | undefined {
  return typeof error === "object" && error !== null && "code" in error && typeof (error as { readonly code?: unknown }).code === "string"
    ? (error as { readonly code: string }).code
    : undefined;
}

function errorCause(error: unknown): unknown {
  return typeof error === "object" && error !== null && "cause" in error ? (error as { readonly cause?: unknown }).cause : undefined;
}

function expectedRecord(env: NodeJS.ProcessEnv): { readonly recordId: string; readonly factDigest: string } | undefined {
  const recordId = text(env, "PERSISTENCE_ACCEPTANCE_RECORD_ID"), factDigest = text(env, "PERSISTENCE_ACCEPTANCE_FACT_DIGEST");
  return recordId !== undefined && /^core-persistence-[a-z0-9-]{8,80}$/.test(recordId) && factDigest !== undefined && /^[a-f0-9]{64}$/.test(factDigest) ? { recordId, factDigest } : undefined;
}
function acceptanceTable(schema: string): string { if (!/^[a-z][a-z0-9_]{0,62}$/.test(schema)) throw new TypeError("CORE_SERVER_PERSISTENCE_SCHEMA_INVALID"); return `"${schema}"."core_server_persistence_acceptance"`; }
function accepted(code: string): void { console.log(JSON.stringify({ verdict: "accepted", code })); }
function rejected(code: string): void { console.error(JSON.stringify({ verdict: "rejected", code })); process.exitCode = 1; }
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceRestoreVerifier();
