import { Signer } from "@aws-sdk/rds-signer";

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
