import { Pool, type PoolClient, type QueryResult, type QueryResultRow } from "pg";
import type { PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { observePostgreSqlOperation } from "./errors";
import type { PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { observeBoundary } from "./observations";

export interface PostgreSqlConnectionCredentials {
  readonly username: string;
  readonly password: string;
  readonly certificateAuthority: string;
}

/** Supplies one opaque provider authentication value for each physical client. */
export interface PostgreSqlTokenConnectionCredentials {
  readonly username: string;
  readonly authenticationToken: () => Promise<string>;
  readonly certificateAuthority: string;
}

export interface PostgreSqlStatement {
  readonly text: string;
  readonly values?: readonly unknown[];
}

export interface PostgreSqlQueryClient {
  query<TRow extends QueryResultRow = QueryResultRow>(statement: PostgreSqlStatement): Promise<QueryResult<TRow>>;
}

export interface PostgreSqlTransactionalClient extends PostgreSqlQueryClient {
  release(): void;
}

export interface PostgreSqlConnectionPool extends PostgreSqlQueryClient {
  connect(): Promise<PostgreSqlTransactionalClient>;
  end(): Promise<void>;
}

export function createNodePostgreSqlConnectionPool(
  configuration: PostgreSqlPersistenceConfiguration,
  credentials: PostgreSqlConnectionCredentials,
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): PostgreSqlConnectionPool {
  const pool = new Pool({
    host: configuration.host,
    port: configuration.port,
    database: configuration.database,
    user: credentials.username,
    password: credentials.password,
    max: configuration.maximumPoolSize,
    connectionTimeoutMillis: configuration.connectionTimeoutMs,
    idleTimeoutMillis: configuration.idleTimeoutMs,
    options: `-c statement_timeout=${configuration.statementTimeoutMs}`,
    ssl: {
      rejectUnauthorized: true,
      ca: credentials.certificateAuthority,
      servername: configuration.host,
    },
  });
  return nodePoolAdapter(pool, diagnostics);
}

export function createNodePostgreSqlTokenConnectionPool(
  configuration: PostgreSqlPersistenceConfiguration,
  credentials: PostgreSqlTokenConnectionCredentials,
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): PostgreSqlConnectionPool {
  const pool = new Pool({
    host: configuration.host,
    port: configuration.port,
    database: configuration.database,
    user: credentials.username,
    password: () => observePostgreSqlOperation("authentication_value", credentials.authenticationToken),
    max: configuration.maximumPoolSize,
    connectionTimeoutMillis: configuration.connectionTimeoutMs,
    idleTimeoutMillis: configuration.idleTimeoutMs,
    options: `-c statement_timeout=${configuration.statementTimeoutMs}`,
    ssl: {
      rejectUnauthorized: true,
      ca: credentials.certificateAuthority,
      servername: configuration.host,
    },
  });
  return nodePoolAdapter(pool, diagnostics);
}

export function nodePoolAdapter(pool: Pool, diagnostics?: PlatformPersistenceDiagnosticOptions): PostgreSqlConnectionPool {
  // `pg` emits an error when an idle client is terminated by PostgreSQL (for
  // example after urgent runtime-credential revocation). Without an error
  // listener Node treats that provider event as unhandled and terminates the
  // server. The next readiness query is still allowed to fail safely and
  // report not-ready; this listener only preserves the process boundary.
  // Deliberately do not log the provider error here: its message can contain
  // provider-controlled detail and diagnostics are emitted by the owning
  // runtime through its safe diagnostic policy.
  pool.on("error", (cause) => { observeBoundary(diagnostics, { operation: "connection-pool", phase: "event", boundary: "idle-pool", condition: "rejected", effect: "not-assessed" }, cause); });
  return {
    query: async (statement) => observePostgreSqlOperation("pool_query", () => nodeQuery(pool, statement)),
    connect: async () => nodeClientAdapter(await observePostgreSqlOperation("pool_connect", () => pool.connect()), diagnostics),
    end: async () => {
      try { return await pool.end(); }
      catch (cause) { observeBoundary(diagnostics, { operation: "connection-pool", phase: "invocation", boundary: "end", condition: "rejected", effect: "not-assessed" }, cause); throw cause; }
    },
  };
}

export function nodeClientAdapter(client: PoolClient, diagnostics?: PlatformPersistenceDiagnosticOptions): PostgreSqlTransactionalClient {
  return {
    query: async (statement) => observePostgreSqlOperation("query", () => nodeQuery(client, statement)),
    release: () => {
      try { return client.release(); }
      catch (cause) { observeBoundary(diagnostics, { operation: "transaction-client", phase: "invocation", boundary: "release", condition: "threw", effect: "not-assessed" }, cause); throw cause; }
    },
  };
}

function nodeQuery<TRow extends QueryResultRow>(
  client: Pick<Pool, "query"> | Pick<PoolClient, "query">,
  statement: PostgreSqlStatement,
): Promise<QueryResult<TRow>> {
  if (statement.values === undefined) return client.query<TRow>(statement.text);
  return client.query<TRow>(statement.text, [...statement.values]);
}
