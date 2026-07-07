import { entityId, type EntityId } from "../src/shared/index";
import {
  fixedTenantResolver,
  tenantContext,
  tenantId,
  type TenantContext,
  type TenantId,
  type TenantResolution,
  type TenantResolver,
} from "../src/tenancy/index";

type PrincipalId = EntityId<"PrincipalId">;

const acceptedTenantId: TenantId = tenantId("tenant-123");
const rejectedPrincipalId: PrincipalId = entityId<"PrincipalId">("principal-456");

const context: TenantContext = tenantContext({ tenantId: acceptedTenantId });
const customIsolationContext: TenantContext = tenantContext({
  tenantId: acceptedTenantId,
  isolationKey: "tenant:tenant-123",
});
const resolution: TenantResolution = context;
const missingResolution: TenantResolution = null;
const resolver: TenantResolver<{ readonly host: string }> = fixedTenantResolver(context);

void context;
void customIsolationContext;
void resolution;
void missingResolution;
void resolver;

// @ts-expect-error tenant IDs must be explicitly branded.
tenantContext({ tenantId: "tenant-123" });

// @ts-expect-error tenant IDs must not accept principal IDs.
tenantContext({ tenantId: rejectedPrincipalId });

// @ts-expect-error tenant resolution is either a tenant context or null.
const invalidResolution: TenantResolution = undefined;
void invalidResolution;
