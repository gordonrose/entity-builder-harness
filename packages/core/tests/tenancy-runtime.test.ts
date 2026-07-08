import { deepEqual, equal } from "node:assert/strict";
import {
  fixedTenantResolver,
  tenantContext,
  tenantId,
  type TenantContext,
} from "../src/tenancy/index";

async function main(): Promise<void> {
  const id = tenantId("tenant-123");
  equal(id, "tenant-123");

  const context = tenantContext({ tenantId: id });
  deepEqual(context, {
    tenantId: "tenant-123",
    isolationKey: "tenant-123",
  });

  const customIsolationContext = tenantContext({
    tenantId: id,
    isolationKey: "tenant:tenant-123",
  });
  deepEqual(customIsolationContext, {
    tenantId: "tenant-123",
    isolationKey: "tenant:tenant-123",
  });

  const resolver = fixedTenantResolver<{ readonly host: string }>(context);
  const resolved = await resolver.resolve({ host: "tenant-123.example.test" });
  deepEqual(resolved, context);

  const missingResolver = fixedTenantResolver<{ readonly host: string }>(null);
  const missing = await missingResolver.resolve({ host: "unknown.example.test" });
  equal(missing, null);

  const acceptedContext: TenantContext = resolved ?? context;
  equal(acceptedContext.tenantId, id);
}

main()
  .then(() => {
    console.log("packages/core tenancy runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
