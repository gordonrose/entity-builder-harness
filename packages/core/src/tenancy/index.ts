import type { EntityId } from "../shared/index";

export type TenantId = EntityId<"TenantId">;

export interface TenantContext {
  readonly tenantId: TenantId;
  readonly isolationKey: string;
}

export interface TenantResolver<TInput> {
  resolve(input: TInput): Promise<TenantContext | null>;
}
