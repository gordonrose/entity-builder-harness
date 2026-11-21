// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.proof-facts
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: code
//   purpose: Hash only the shared original-record fields for independent HTTP and restored-database observations.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createHash } from "node:crypto";

/** Keep the same canonical field order across independent proof transports.
 * Includes the original generated identity and timestamps, not just user facts. */
export function entitySmokeRecordDigest(value: object): string {
  const record = value as Record<string, unknown>;
  const names = ["id", "integerValue", "uuidValue", "occurredAt", "label", "status", "enabled", "categories", "notes", "description", "reviewedAt", "secondaryCategories", "visibility", "lifecycle", "createdAt", "updatedAt"];
  return createHash("sha256").update(JSON.stringify(names.map(name => [name, record[name]]))).digest("hex");
}
