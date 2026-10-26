// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-restore-verifier
//   version: 3
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-26"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Verify a declared synthetic acceptance record in an isolated restored PostgreSQL copy using only the runtime credential.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { createNodePostgreSqlTokenConnectionPool, observePostgreSqlOperation, postgreSqlFailureDiagnostic, type PostgreSqlFailureDiagnostic } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { connect as connectTcp } from "node:net";
import { connect as connectTls } from "node:tls";

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
  const diagnosticMode = text(env, "PERSISTENCE_RESTORE_DIAGNOSTIC_MODE");
  const diagnostic = diagnosticMode === "connection";
  const expected = expectedRecord(env);
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (configuration === undefined || credentials === undefined || (!diagnostic && expected === undefined) || certificateAuthority === undefined || (diagnosticMode !== undefined && !diagnostic)) return rejected("PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID", undefined, diagnostic);
  // Establish the private route and PostgreSQL TLS trust before materialising
  // an IAM token. Neither preflight sends a credential or query.
  try {
    await observePostgreSqlOperation("tcp_probe", () => probePostgreSqlTransport(configuration.host, configuration.port));
  } catch (error) {
    return rejected(restoreTransportFailureCode(error), postgreSqlFailureDiagnostic(error), diagnostic);
  }
  try {
    await observePostgreSqlOperation("tls_probe", () => probePostgreSqlTls(configuration.host, configuration.port, certificateAuthority));
  } catch (error) {
    return rejected(restoreTlsPreflightFailureCode(error), postgreSqlFailureDiagnostic(error), diagnostic);
  }
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { ...credentials, certificateAuthority });
  let client: Awaited<ReturnType<typeof pool.connect>> | undefined;
  try {
    try {
      client = await pool.connect();
    } catch (error) {
      return rejected(postgreSqlFailureDiagnostic(error).facts.phase === "authentication_value" ? "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_UNAVAILABLE" : restoreConnectionFailureCode(error), postgreSqlFailureDiagnostic(error), diagnostic);
    }
    if (diagnostic) {
      await client.query({ text: "SELECT 1" });
      return diagnosed("KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED");
    }
    // Configuration validation above requires this only for recovery proof.
    if (expected === undefined) return rejected("PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID");
    const result = await client.query<{ readonly record_id: string; readonly fact_digest: string }>({
      text: `SELECT record_id, fact_digest FROM ${acceptanceTable(configuration.schema)} WHERE record_id = $1`,
      values: [expected.recordId],
    });
    const row = result.rows[0];
    if (row?.record_id === expected.recordId && row.fact_digest === expected.factDigest) return accepted("KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED");
    return rejected("KANBIEN_CORE_PERSISTENCE_RESTORE_RECORD_MISMATCH");
  } catch (error) {
    return rejected(restoreQueryFailureCode(error), postgreSqlFailureDiagnostic(error), diagnostic);
  } finally {
    client?.release();
    // A failed connection can leave no reusable client. Closing that pool is
    // cleanup only; it must not overwrite the closed diagnostic emitted for
    // token, connection, or query failure.
    try { await pool.end(); } catch { /* safe diagnostic already selected */ }
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
  switch (postgreSqlFailureDiagnostic(error).facts.classification) {
    case "authentication_rejected": return "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED";
    case "permission_denied": return "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED";
    case "content_unavailable": return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE";
    case "transport_unavailable":
    case "timeout": return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE";
    case "tls_trust_invalid": return "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID";
    default: return "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE";
  }
}

/**
 * Unknown connection failures are still safe to distinguish from a query
 * failure. The category is closed: raw driver/provider text never crosses
 * the verifier boundary.
 */
export function restoreConnectionFailureCode(error: unknown): string {
  const classified = restoreVerificationFailureCode(error);
  return classified === "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE"
    ? "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE"
    : classified;
}

/** The preflight has no PostgreSQL credential or query, so it reports only a
 * closed transport boundary when no allowlisted machine code is available. */
export function restoreTransportFailureCode(error: unknown): string {
  const classified = restoreVerificationFailureCode(error);
  return classified === "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE"
    ? "KANBIEN_CORE_PERSISTENCE_RESTORE_TRANSPORT_UNAVAILABLE"
    : classified;
}

export function restoreTlsPreflightFailureCode(error: unknown): string {
  const classified = restoreVerificationFailureCode(error);
  return classified === "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE"
    ? "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_NEGOTIATION_UNAVAILABLE"
    : classified;
}

/** A separate probe establishes no internal stage of this connection. */
export function restorePostTransportConnectionFailureCode(error: unknown): string {
  return restoreConnectionFailureCode(error);
}

/**
 * Probe only DNS and TCP reachability. PostgreSQL TLS negotiation deliberately
 * remains in the authenticated driver path, where its closed allowlisted
 * machine codes are classified separately. The socket is never sent a
 * credential or a PostgreSQL query.
 */
export function probePostgreSqlTransport(host: string, port: number, timeoutMs = 5_000): Promise<void> {
  return new Promise((resolve, reject) => {
    const socket = connectTcp({ host, port });
    let completed = false;
    const finish = (callback: () => void) => {
      if (completed) return;
      completed = true;
      clearTimeout(timeout);
      callback();
    };
    const timeout = setTimeout(() => {
      const error = new Error("transport timeout") as Error & { code: string };
      error.code = "ETIMEDOUT";
      socket.destroy(error);
    }, timeoutMs);
    socket.once("connect", () => {
      finish(resolve);
      socket.destroy();
    });
    socket.once("error", (error) => finish(() => reject(error)));
  });
}

/**
 * PostgreSQL requires an SSLRequest before TLS. This probe performs only that
 * negotiation and certificate validation; it never sends a role, token,
 * password, database name, or SQL statement.
 */
export function probePostgreSqlTls(host: string, port: number, certificateAuthority: string, timeoutMs = 5_000): Promise<void> {
  return new Promise((resolve, reject) => {
    const socket = connectTcp({ host, port });
    let completed = false;
    const finish = (callback: () => void) => { if (completed) return; completed = true; clearTimeout(timeout); callback(); };
    const timeout = setTimeout(() => {
      const error = new Error("tls negotiation timeout") as Error & { code: string };
      error.code = "ETIMEDOUT";
      socket.destroy(error);
    }, timeoutMs);
    socket.once("connect", () => socket.write(Buffer.from([0, 0, 0, 8, 4, 210, 22, 47])));
    socket.once("data", (response: Buffer) => {
      if (response.length !== 1 || response[0] !== 83) {
        const error = new Error("postgresql tls unavailable") as Error & { code: string };
        error.code = "POSTGRES_TLS_UNAVAILABLE";
        socket.destroy(error);
        return;
      }
      const tlsSocket = connectTls({ socket, servername: host, ca: certificateAuthority, rejectUnauthorized: true });
      tlsSocket.once("secureConnect", () => { finish(resolve); tlsSocket.destroy(); });
      tlsSocket.once("error", (error) => finish(() => reject(error)));
    });
    socket.once("error", (error) => finish(() => reject(error)));
  });
}

/**
 * A connection can succeed while the restored data is unavailable. Preserve
 * allowlisted PostgreSQL/TLS classifications, otherwise use this closed query
 * category so the governed controller can direct the next diagnosis safely.
 */
export function restoreQueryFailureCode(error: unknown): string {
  const classified = restoreVerificationFailureCode(error);
  return classified === "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE"
    ? "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE"
    : classified;
}

function expectedRecord(env: NodeJS.ProcessEnv): { readonly recordId: string; readonly factDigest: string } | undefined {
  const recordId = text(env, "PERSISTENCE_ACCEPTANCE_RECORD_ID"), factDigest = text(env, "PERSISTENCE_ACCEPTANCE_FACT_DIGEST");
  return recordId !== undefined && /^core-persistence-[a-z0-9-]{8,80}$/.test(recordId) && factDigest !== undefined && /^[a-f0-9]{64}$/.test(factDigest) ? { recordId, factDigest } : undefined;
}
function acceptanceTable(schema: string): string { if (!/^[a-z][a-z0-9_]{0,62}$/.test(schema)) throw new TypeError("CORE_SERVER_PERSISTENCE_SCHEMA_INVALID"); return `"${schema}"."core_server_persistence_acceptance"`; }
const resultSchema = "deploy/persistence-restore-verifier-result/v2";
function accepted(code: string): void { console.log(JSON.stringify({ schema: resultSchema, verdict: "accepted", code })); }
function diagnosed(code: string): void { console.log(JSON.stringify({ schema: resultSchema, verdict: "diagnosed", code })); }
function rejected(code: string, diagnostic?: PostgreSqlFailureDiagnostic, connectionDiagnostic = false): void {
  console.error(JSON.stringify({ schema: resultSchema, verdict: connectionDiagnostic ? "diagnostic-failed" : "rejected", code, ...(diagnostic === undefined ? {} : { execution: diagnostic.facts }) }));
  process.exitCode = 1;
}
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceRestoreVerifier();
