import type { Permission } from "@kanbien/core/authz";
import {
  definePlatformApp,
  platformAppId,
  platformRouteName,
  type PlatformResponse,
} from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import {
  createPlatformServerShell,
  type PlatformServerAuthHook,
  type PlatformServerMiddlewareStep,
  type PlatformServerResponse,
} from "../src/index";

const appId = platformAppId("smoke");
const routeName = platformRouteName("smoke.echo");
if (!appId.ok || !routeName.ok) {
  throw new Error("Expected valid server type primitives.");
}

const permission = "smoke:read" as Permission;
const auth: PlatformServerAuthHook = {
  authenticate: () => ({ authenticated: true, permissions: [permission] }),
};
const app = definePlatformApp({
  id: appId.value,
  name: "Smoke",
  mount(registry) {
    registry.registerPermission({ permission });
    registry.registerRoute({
      name: routeName.value,
      method: "GET",
      path: "/echo",
      auth: { kind: "authenticated", permissions: [permission] },
      handler: {
        handle: (): PlatformResponse => ({ status: 200 }),
      },
    });
  },
});

const shell = createPlatformServerShell({ apps: [app], deps: createPlatformTestMountDeps(), auth });
void shell;

const response: PlatformServerResponse = {
  status: 200,
  headers: {},
  middleware: ["request-id", "handler"] satisfies readonly PlatformServerMiddlewareStep[],
};
void response;

// @ts-expect-error server requests are constrained to known HTTP methods.
createPlatformServerShell({ apps: [app], deps: createPlatformTestMountDeps() }).then((created) => created.ok && created.value.handle({ method: "TRACE", path: "/x" }));

// @ts-expect-error auth hook permissions use core Permission values.
const invalidAuth: PlatformServerAuthHook = { authenticate: () => ({ authenticated: true, permissions: [123] }) };
void invalidAuth;
