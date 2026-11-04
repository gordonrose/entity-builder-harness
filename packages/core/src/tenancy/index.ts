import { entityId, type EntityId } from "../shared/index";
import { TenantObservation } from "./observations";
import type { CoreTenancyDiagnosticOptions } from "./diagnostics";
export { coreTenancyBoundaryDiagnostic, coreTenancyBoundaryDiagnosticRecord, coreTenancyDiagnosticDefinitions } from "./diagnostics";
export type { CoreTenancyBoundaryDetail, CoreTenancyDiagnosticOptions } from "./diagnostics";
export { observeCoreTenancyDiagnostic } from "./observations";

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
}, diagnostics?: CoreTenancyDiagnosticOptions): TenantContext {
  const observation = new TenantObservation(diagnostics);
  return observation.run(() => ({
    tenantId: observation.read("tenant-id", () => input.tenantId),
    isolationKey: observation.read("isolation-key", () => input.isolationKey) ?? observation.read("tenant-id", () => input.tenantId),
  }));
}

export function fixedTenantResolver<TInput>(resolution: TenantResolution): TenantResolver<TInput> {
  return {
    resolve: async () => resolution,
  };
}
