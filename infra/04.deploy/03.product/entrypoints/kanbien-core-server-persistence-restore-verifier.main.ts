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

import { createNodePostgreSqlTokenConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
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
  const expected = expectedRecord(env);
  const certificateAuthority = persistenceCertificateAuthority(env);
  if (configuration === undefined || credentials === undefined || expected === undefined || certificateAuthority === undefined) return rejected("PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID");
  // Establish the private route and PostgreSQL TLS trust before materialising
  // an IAM token. Neither preflight sends a credential or query.
  try {
    await probePostgreSqlTransport(configuration.host, configuration.port);
  } catch (error) {
    return rejected(restoreTransportFailureCode(error));
  }
  try {
    await probePostgreSqlTls(configuration.host, configuration.port, certificateAuthority);
  } catch (error) {
    return rejected(restoreTlsPreflightFailureCode(error));
  }
  let token: string;
  try {
    token = await credentials.authenticationToken();
  } catch {
    return rejected("KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_UNAVAILABLE");
  }
  const pool = createNodePostgreSqlTokenConnectionPool(configuration, { username: credentials.username, authenticationToken: async () => token, certificateAuthority });
  let client: Awaited<ReturnType<typeof pool.connect>> | undefined;
  try {
    try {
      client = await pool.connect();
    } catch (error) {
      return rejected(restorePostTransportConnectionFailureCode(error));
    }
    const result = await client.query<{ readonly record_id: string; readonly fact_digest: string }>({
      text: `SELECT record_id, fact_digest FROM ${acceptanceTable(configuration.schema)} WHERE record_id = $1`,
      values: [expected.recordId],
    });
    const row = result.rows[0];
    if (row?.record_id === expected.recordId && row.fact_digest === expected.factDigest) return accepted("KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED");
    return rejected("KANBIEN_CORE_PERSISTENCE_RESTORE_RECORD_MISMATCH");
  } catch (error) {
    return rejected(restoreQueryFailureCode(error));
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
  // `pg`, Node TLS, and a small number of AWS client wrappers can retain the
  // useful machine code on a causal or aggregate error. Read only those
  // closed fields: never turn a provider message, endpoint, query, or
  // credential-bearing value into a result code.
  const codes = errorCodes(error);
  if (codes.some((code) => code === "28P01" || code === "28000")) return "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED";
  if (codes.includes("42501")) return "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED";
  if (codes.some((code) => code === "3D000" || code === "42P01")) return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE";
  if (codes.some((code) => code === "ECONNREFUSED" || code === "ECONNRESET" || code === "ETIMEDOUT" || code === "EHOSTUNREACH" || code === "ENETUNREACH" || code === "EAI_AGAIN" || code === "ENOTFOUND")) return "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE";
  if (codes.some((code) => code === "CERT_HAS_EXPIRED" || code === "ERR_TLS_CERT_ALTNAME_INVALID" || code === "SELF_SIGNED_CERT_IN_CHAIN" || code === "UNABLE_TO_VERIFY_LEAF_SIGNATURE")) return "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID";
  return "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE";
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

/**
 * A completed TCP preflight proves that an opaque subsequent pool failure is
 * not simply an absent route to the database port.  Keep the unknown result
 * closed: the controller can request a bounded PostgreSQL/TLS correction
 * without receiving raw driver detail.
 */
export function restorePostTransportConnectionFailureCode(error: unknown): string {
  const classified = restoreVerificationFailureCode(error);
  return classified === "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE"
    ? "KANBIEN_CORE_PERSISTENCE_RESTORE_DATABASE_HANDSHAKE_UNAVAILABLE"
    : classified;
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

function errorCodes(error: unknown, depth = 0, seen = new Set<object>()): readonly string[] {
  if (depth > 3 || typeof error !== "object" || error === null || seen.has(error)) return [];
  seen.add(error);
  const value = error as { readonly code?: unknown; readonly cause?: unknown; readonly errors?: unknown };
  const direct = typeof value.code === "string" ? [value.code] : [];
  const causal = errorCodes(value.cause, depth + 1, seen);
  const aggregate = Array.isArray(value.errors)
    ? value.errors.flatMap((nested) => errorCodes(nested, depth + 1, seen))
    : [];
  return [...direct, ...causal, ...aggregate];
}

function expectedRecord(env: NodeJS.ProcessEnv): { readonly recordId: string; readonly factDigest: string } | undefined {
  const recordId = text(env, "PERSISTENCE_ACCEPTANCE_RECORD_ID"), factDigest = text(env, "PERSISTENCE_ACCEPTANCE_FACT_DIGEST");
  return recordId !== undefined && /^core-persistence-[a-z0-9-]{8,80}$/.test(recordId) && factDigest !== undefined && /^[a-f0-9]{64}$/.test(factDigest) ? { recordId, factDigest } : undefined;
}
function acceptanceTable(schema: string): string { if (!/^[a-z][a-z0-9_]{0,62}$/.test(schema)) throw new TypeError("CORE_SERVER_PERSISTENCE_SCHEMA_INVALID"); return `"${schema}"."core_server_persistence_acceptance"`; }
function accepted(code: string): void { console.log(JSON.stringify({ verdict: "accepted", code })); }
function rejected(code: string): void { console.error(JSON.stringify({ verdict: "rejected", code })); process.exitCode = 1; }
if (typeof require !== "undefined" && require.main === module) void runKanbienCoreServerPersistenceRestoreVerifier();
