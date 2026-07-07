import { entityId, type EntityId } from "../shared/index";

export type TenantId = EntityId<"TenantId">;
export type TenantResolution = TenantContext | null;

export interface TenantContext {
  readonly tenantId: TenantId;
  readonly isolationKey: string;
}

export interface TenantResolver<TInput> {
  resolve(input: TInput): Promise<TenantResolution>;
}

export function tenantId(value: string): TenantId {
  return entityId<"TenantId">(value);
}

export function tenantContext(input: {
  readonly tenantId: TenantId;
  readonly isolationKey?: string;
}): TenantContext {
  return {
    tenantId: input.tenantId,
    isolationKey: input.isolationKey ?? input.tenantId,
  };
}

export function fixedTenantResolver<TInput>(resolution: TenantResolution): TenantResolver<TInput> {
  return {
    resolve: async () => resolution,
  };
}
