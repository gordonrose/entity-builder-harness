// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-iam-authentication
//   version: 3
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-27"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: code
//   purpose: Bind target-owned RDS IAM database authentication to persistence workload identities without retrieving a database password.
//   portability: { class: internal, targets: [kanbien-core-platform] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-administration
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts

import { rdsIamAuthenticationToken, rdsIamAuthenticationTextRules, type PostgreSqlPersistenceConfiguration } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { recordConfigSource, validateConfigSettings } from "@kanbien/core/config";
import { persistenceConfigurationFailure, persistenceIamConfigurationDiagnostic } from "./kanbien-core-server-persistence-configuration";

export type PersistenceIamAuthentication = { readonly username: string; readonly authenticationToken: () => Promise<string> };

export function persistenceIamAuthenticationResult(
  env: NodeJS.ProcessEnv,
  configuration: PostgreSqlPersistenceConfiguration,
  usernameKey: string,
) {
  const checked = validateConfigSettings(recordConfigSource(env), [
    { setting: "authentication.username", source: usernameKey, rule: rdsIamAuthenticationTextRules.username },
    { setting: "authentication.region", source: "PERSISTENCE_POSTGRES_IAM_REGION", rule: rdsIamAuthenticationTextRules.region },
  ]);
  if (!checked.ok) return persistenceConfigurationFailure(checked.error.issues, persistenceIamConfigurationDiagnostic);
  const username = checked.value["authentication.username"] as string;
  const region = checked.value["authentication.region"] as string;
  // Disposable-package qualification has no RDS IAM endpoint. Its synthetic
  // token is allowed only with the explicit test runtime marker; target
  // declarations reject both variables for any deployed workload.
  const localToken = text(env["PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN"]);
  const localDelayText = text(env["PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN_DELAY_MS"]);
  const localDelay = localDelayText === undefined ? 0 : Number(localDelayText);
  if (env["NODE_ENV"] === "test" && localToken !== undefined && Number.isInteger(localDelay) && localDelay >= 0 && localDelay <= 10_000) {
    return { ok: true as const, value: {
      username,
      authenticationToken: async () => {
        if (localDelay > 0) await new Promise<void>((resolve) => setTimeout(resolve, localDelay));
        return localToken;
      },
    } };
  }
  return { ok: true as const, value: { username, authenticationToken: rdsIamAuthenticationToken({ region, hostname: configuration.host, port: configuration.port, username }) } };
}

/** Compatibility reader; production entrypoints retain the structured result. */
export function persistenceIamAuthentication(env: NodeJS.ProcessEnv, configuration: PostgreSqlPersistenceConfiguration, usernameKey: string): PersistenceIamAuthentication | undefined {
  const checked = persistenceIamAuthenticationResult(env, configuration, usernameKey);
  return checked.ok ? checked.value : undefined;
}

function text(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined;
}
