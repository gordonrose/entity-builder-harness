// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.shared-scheduling-configuration
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [security, sre]
//   kind: code
//   purpose: Bind checked scheduling configuration to one scope and one independent workload identity.
//   portability: { class: internal, targets: [kanbien-core-platform, entity-smoke] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.shared-scheduling-invocation
//     path: infra/04.deploy/03.product/entrypoints/shared/scheduling/invocation.ts

import { recordConfigSource, validateConfigSettings, type ConfigSettingIssue } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { validateSqsSenderConfiguration } from "@kanbien/platform-adapter-aws-queue-sqs";
import { rdsIamAuthenticationTextRules } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { persistenceCertificateAuthorityResult, persistenceConfigurationFailure, persistenceConfigurationResult } from "../persistence/configuration";
import { persistenceIamAuthenticationResult } from "../../kanbien-core-server-persistence-iam-authentication";
import { schedulingTargetConfigurationDiagnostic } from "./diagnostics";

export type SchedulingPurpose = "dispatch" | "worker";
export interface SchedulingScopeConfiguration {
  readonly schema: string;
  readonly dispatchUsername: string;
  readonly workerUsername: string;
}

/** Fixed program bindings, not event-supplied target selection. No clients are opened here. */
export function schedulingConfiguration(env: NodeJS.ProcessEnv, scope: SchedulingScopeConfiguration,
  purpose: SchedulingPurpose, readCertificate?: (path: string) => string) {
  const persistence = schedulingRequired(persistenceConfigurationResult(env, "scheduled"));
  const credentials = schedulingRequired(persistenceIamAuthenticationResult(env, persistence, "PERSISTENCE_SCHEDULING_DATABASE_USERNAME"));
  const queue = schedulingRequired(validateSqsSenderConfiguration({ get(setting) {
    return env[setting === "queue.address" ? "SCHEDULING_QUEUE_URL" : "AWS_REGION"];
  } }));
  const fields = validateConfigSettings(recordConfigSource({ arn: env["SCHEDULING_QUEUE_ARN"], region: queue.region }), [
    { setting: "queue.arn", source: "arn", rule: { kind: "text", pattern: /^arn:aws:sqs:[a-z0-9-]+:\d{12}:[A-Za-z0-9_-]{1,80}$/ } },
    { setting: "queue.region", source: "region", rule: rdsIamAuthenticationTextRules.region },
  ]);
  if (!fields.ok) throw persistenceConfigurationFailure(fields.error.issues, schedulingTargetConfigurationDiagnostic).error;
  const queueArn = fields.value["queue.arn"] as string;
  const region = fields.value["queue.region"] as string;
  const [, , , queueRegion, account, queueName] = queueArn.split(":");
  const expectedUsername = purpose === "dispatch" ? scope.dispatchUsername : scope.workerUsername;
  const reference = persistence.runtimeCredentialSecretReference.split(":");
  const issues: ConfigSettingIssue[] = [];
  const mismatch = (setting: string) => issues.push({ setting, reason: "inconsistent-settings" });
  if (persistence.schema !== scope.schema) mismatch("database.schema");
  if (credentials.username !== expectedUsername) mismatch("authentication.username");
  if (reference[1] !== "aws" || reference[2] !== "rds-db" || reference[3] !== region || reference[4] !== account
    || reference[5] !== "dbuser" || !reference[6]?.endsWith(`/${expectedUsername}`)
    || credentials.region !== region) mismatch("authentication.reference");
  if (queueRegion !== region) mismatch("queue.region");
  if (queue.queueUrl !== `https://sqs.${region}.amazonaws.com/${account}/${queueName}`) mismatch("queue.address");
  if (issues.length > 0) throw persistenceConfigurationFailure(issues, schedulingTargetConfigurationDiagnostic).error;
  const certificateAuthority = schedulingRequired(persistenceCertificateAuthorityResult(env, readCertificate));
  return { persistence, credentials: { ...credentials, certificateAuthority }, queue: { ...queue, region, queueArn } };
}
export type SchedulingConfiguration = ReturnType<typeof schedulingConfiguration>;
export function schedulingRequired<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }
