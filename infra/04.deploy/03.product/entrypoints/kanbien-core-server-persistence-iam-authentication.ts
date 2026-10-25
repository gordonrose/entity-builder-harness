// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-iam-authentication
//   version: 1
//   status: draft
//   created_on: "2026-10-25"
//   updated_on: "2026-10-25"
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

import { rdsIamAuthenticationToken, type PostgreSqlPersistenceConfiguration } from "@kanbien/platform-adapter-aws-persistence-postgresql";

export function persistenceIamAuthentication(
  env: NodeJS.ProcessEnv,
  configuration: PostgreSqlPersistenceConfiguration,
  usernameKey: string,
): { readonly username: string; readonly authenticationToken: () => Promise<string> } | undefined {
  const username = text(env[usernameKey]);
  const region = text(env["PERSISTENCE_POSTGRES_IAM_REGION"]);
  if (username === undefined || region === undefined || !/^[a-z_][a-z0-9_]{0,62}$/.test(username) || !/^[a-z]{2}-[a-z]+-\d$/.test(region)) return undefined;
  // Disposable-package qualification has no RDS IAM endpoint. Its synthetic
  // token is allowed only with the explicit test runtime marker; target
  // declarations reject both variables for any deployed workload.
  const localToken = text(env["PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN"]);
  if (env["NODE_ENV"] === "test" && localToken !== undefined) return { username, authenticationToken: async () => localToken };
  return { username, authenticationToken: rdsIamAuthenticationToken({ region, hostname: configuration.host, port: configuration.port, username }) };
}

function text(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() !== "" && value.trim() === value ? value : undefined;
}
