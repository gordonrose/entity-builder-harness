import { Signer } from "@aws-sdk/rds-signer";
import type { ConfigSettingRule } from "@kanbien/core/config";
import { postgreSqlLoginNameRule } from "./configuration/index";

/** Lexical acceptance rules, not evidence that an identity or region exists. */
export const rdsIamAuthenticationTextRules = {
  username: postgreSqlLoginNameRule,
  region: { kind: "text", pattern: /^[a-z]{2}-[a-z]+-\d$/ },
} as const satisfies Readonly<Record<"username" | "region", ConfigSettingRule>>;

export interface RdsIamAuthenticationTokenOptions {
  readonly region: string;
  readonly hostname: string;
  readonly port: number;
  readonly username: string;
}

/** Return opaque RDS IAM database tokens only to the PostgreSQL driver. */
export function rdsIamAuthenticationToken(options: RdsIamAuthenticationTokenOptions): () => Promise<string> {
  const signer = new Signer({
    region: options.region,
    hostname: options.hostname,
    port: options.port,
    username: options.username,
  });
  return async () => signer.getAuthToken();
}
