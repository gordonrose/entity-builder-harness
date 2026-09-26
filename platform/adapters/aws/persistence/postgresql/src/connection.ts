import { Pool, type PoolClient, type QueryResult, type QueryResultRow } from "pg";
import type { PostgreSqlPersistenceConfiguration } from "./config";

export interface PostgreSqlConnectionCredentials {
  readonly username: string;
  readonly password: string;
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
  return nodePoolAdapter(pool);
}

export function nodePoolAdapter(pool: Pool): PostgreSqlConnectionPool {
  return {
    query: async (statement) => nodeQuery(pool, statement),
    connect: async () => nodeClientAdapter(await pool.connect()),
    end: async () => pool.end(),
  };
}

export function nodeClientAdapter(client: PoolClient): PostgreSqlTransactionalClient {
  return {
    query: async (statement) => nodeQuery(client, statement),
    release: () => client.release(),
  };
}

function nodeQuery<TRow extends QueryResultRow>(
  client: Pick<Pool, "query"> | Pick<PoolClient, "query">,
  statement: PostgreSqlStatement,
): Promise<QueryResult<TRow>> {
  if (statement.values === undefined) return client.query<TRow>(statement.text);
  return client.query<TRow>(statement.text, [...statement.values]);
}
