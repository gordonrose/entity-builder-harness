import type { EntityId } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type PrincipalId = EntityId<"PrincipalId">;

export interface Principal {
  readonly id: PrincipalId;
  readonly tenantId?: TenantId;
  readonly subject: string;
  readonly claims: Readonly<Record<string, unknown>>;
}

export interface Authenticator<TCredential> {
  authenticate(credential: TCredential): Promise<Principal | null>;
}
