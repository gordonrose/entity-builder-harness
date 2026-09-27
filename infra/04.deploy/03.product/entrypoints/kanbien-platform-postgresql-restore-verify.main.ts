// Verify the one fixed harmless smoke record on an isolated restored database.
// The host is supplied only by the governed recovery runner and is restricted
// to the reviewed staging RDS recovery-name pattern before a TLS connection.

import { outboxEntryId } from "@kanbien/core/persistence";
import { closePool, configurationFromEnvironment, connectionPool, secretFromEnvironment, writeOutcome } from "./kanbien-platform-postgresql-task";

const fixedWorkItem = "postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  try {
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const restoreHost = restoreHostFromEnvironment();
    pool = connectionPool({ ...runtime, host: restoreHost }, configuration.runtimeSecretArn, configuration.schema);
    const workItem = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_smoke_work_item" WHERE id = $1 AND state = $2',
      values: [fixedWorkItem, "accepted"],
    });
    const outbox = await pool.query<{ readonly count: string }>({
      text: 'SELECT COUNT(*)::text AS count FROM "platform_smoke"."platform_outbox" WHERE id = $1',
      values: [String(outboxEntryId("platform-smoke.work-item-accepted." + fixedWorkItem))],
    });
    if (workItem.rows[0]?.count !== "1" || outbox.rows[0]?.count !== "1") throw new Error("RELATIONAL_RESTORE_PROOF_NOT_FOUND");
    writeOutcome("restore_verified", "succeeded");
  } catch {
    writeOutcome("restore_verified", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

function restoreHostFromEnvironment(): string {
  const candidate = process.env["RELATIONAL_RESTORE_HOST"];
  if (candidate === undefined || !/^kanbien-staging-platform-relational-restore-proof-[a-z0-9-]+\.[a-z0-9-]+\.eu-west-1\.rds\.amazonaws\.com$/.test(candidate)) {
    throw new Error("RELATIONAL_RESTORE_HOST_INVALID");
  }
  return candidate;
}

void main();
