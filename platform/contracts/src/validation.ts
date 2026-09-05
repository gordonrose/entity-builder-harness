import type { Permission } from "@kanbien/core/authz";
import type { JsonValue, Result } from "@kanbien/core/shared";
import type { Validator } from "@kanbien/core/validation";
import type { PlatformPermissionDeclaration } from "./app";
import {
  invalidContractName,
  malformedPlatformJob,
  malformedPlatformPermission,
  malformedPlatformRoute,
  reservedPlatformPath,
  unknownPlatformPermission,
  type PlatformContractError,
} from "./errors";
import { isPlatformContractName } from "./identifiers";
import type { PlatformJobRegistration } from "./jobs";
import type {
  HttpMethod,
  PlatformResourceAuthorization,
  PlatformRouteRegistration,
  PlatformTenantRequirement,
  RouteAuthRequirement,
} from "./routes";

export const defaultReservedPlatformRoutePaths: readonly string[] = ["/", "/livez", "/readyz", "/health", "/metrics", "/admin"];

export interface PlatformRouteValidationOptions {
  readonly declaredPermissions?: readonly Permission[];
  readonly reservedPaths?: readonly string[];
}

export function validatePlatformPermissionDeclaration(
  declaration: PlatformPermissionDeclaration,
): Result<void, PlatformContractError> {
  if (!isRecord(declaration)) {
    return contractFailure(malformedPlatformPermission("Permission declaration must be an object."));
  }

  const declaredPermission = declaration["permission"];
  if (!isPermission(declaredPermission)) {
    return contractFailure(
      malformedPlatformPermission("Permission declarations must use core resource:action permission strings.", {
        permission: stringifyDetail(declaredPermission),
      }),
    );
  }

  return contractSuccess();
}

export function validatePlatformRouteRegistration(
  route: PlatformRouteRegistration,
  options: PlatformRouteValidationOptions = {},
): Result<void, PlatformContractError> {
  if (!isRecord(route)) {
    return contractFailure(malformedPlatformRoute("Route registration must be an object."));
  }

  const routeName = route["name"];
  if (!isPlatformContractName(routeName)) {
    return contractFailure(invalidContractName("platform route name", routeName));
  }

  const method = route["method"];
  if (!isHttpMethod(method)) {
    return contractFailure(malformedPlatformRoute("Route method must be a supported HTTP method.", { method: stringifyDetail(method) }));
  }

  const path = route["path"];
  if (!isRoutePath(path)) {
    return contractFailure(malformedPlatformRoute("Route path must be an absolute path without whitespace or URL scheme.", { path: stringifyDetail(path) }));
  }

  const reservedPath = findReservedPlatformRoutePath(path, options.reservedPaths ?? defaultReservedPlatformRoutePaths);
  if (reservedPath !== undefined) {
    return contractFailure(reservedPlatformPath(path, reservedPath));
  }

  const auth = route["auth"];
  if (!isRouteAuthRequirement(auth)) {
    return contractFailure(malformedPlatformRoute("Route auth requirement must be public or authenticated."));
  }

  const tenantRequirement = route["tenant"];
  if (tenantRequirement !== undefined && !isTenantRequirement(tenantRequirement)) {
    return contractFailure(malformedPlatformRoute("Route tenant requirement must be optional or required."));
  }

  const resourceAuthorization = route["resourceAuthorization"];
  if (resourceAuthorization !== undefined && !isPlatformResourceAuthorization(resourceAuthorization)) {
    return contractFailure(malformedPlatformRoute("Route resource authorization must declare a permission and resolve function."));
  }

  if (auth.kind === "public" && (tenantRequirement !== undefined || resourceAuthorization !== undefined)) {
    return contractFailure(malformedPlatformRoute("Public routes cannot declare tenant or resource authorization controls."));
  }

  if (auth.kind === "authenticated") {
    const routePermissions = auth.permissions ?? [];
    for (const routePermission of routePermissions) {
      if (!isPermission(routePermission)) {
        return contractFailure(
          malformedPlatformRoute("Route permissions must use core resource:action permission strings.", {
            permission: stringifyDetail(routePermission),
          }),
        );
      }

      if (options.declaredPermissions !== undefined && !options.declaredPermissions.includes(routePermission)) {
        return contractFailure(unknownPlatformPermission(routePermission, options.declaredPermissions));
      }
    }

    if (resourceAuthorization !== undefined) {
      if (!isPermission(resourceAuthorization.permission)) {
        return contractFailure(
          malformedPlatformRoute("Route resource authorization permission must use a core resource:action permission string.", {
            permission: stringifyDetail(resourceAuthorization.permission),
          }),
        );
      }

      if (options.declaredPermissions !== undefined && !options.declaredPermissions.includes(resourceAuthorization.permission)) {
        return contractFailure(unknownPlatformPermission(resourceAuthorization.permission, options.declaredPermissions));
      }
    }
  }

  const validator = route["validator"];
  if (validator !== undefined && !isValidator(validator)) {
    return contractFailure(malformedPlatformRoute("Route validator must implement the core Validator contract."));
  }

  if (!isHandler(route["handler"])) {
    return contractFailure(malformedPlatformRoute("Route handler must expose a handle function."));
  }

  return contractSuccess();
}

export function validatePlatformJobRegistration(job: PlatformJobRegistration): Result<void, PlatformContractError> {
  if (!isRecord(job)) {
    return contractFailure(malformedPlatformJob("Job registration must be an object."));
  }

  const jobName = job["name"];
  if (!isPlatformContractName(jobName)) {
    return contractFailure(invalidContractName("platform job name", jobName));
  }

  const messageType = job["messageType"];
  if (!isPlatformContractName(messageType)) {
    return contractFailure(
      malformedPlatformJob("Job message type must use dot-separated lowercase segments.", {
        messageType: stringifyDetail(messageType),
      }),
    );
  }

  const validator = job["validator"];
  if (validator !== undefined && !isValidator(validator)) {
    return contractFailure(malformedPlatformJob("Job validator must implement the core Validator contract."));
  }

  if (!isHandler(job["handler"])) {
    return contractFailure(malformedPlatformJob("Job handler must expose a handle function."));
  }

  return contractSuccess();
}

function contractSuccess(): Result<void, PlatformContractError> {
  return { ok: true, value: undefined };
}

function contractFailure(error: PlatformContractError): Result<void, PlatformContractError> {
  return { ok: false, error };
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null;
}

function isPermission(value: unknown): value is Permission {
  return typeof value === "string" && permissionPattern.test(value);
}

function isHttpMethod(value: unknown): value is HttpMethod {
  return typeof value === "string" && httpMethods.includes(value as HttpMethod);
}

function isRoutePath(value: unknown): value is string {
  return typeof value === "string" && value.startsWith("/") && !/\s/.test(value) && !value.includes("://");
}

function findReservedPlatformRoutePath(path: string, reservedPaths: readonly string[]): string | undefined {
  return reservedPaths.find((reservedPath) => pathMatchesReservedPath(path, reservedPath));
}

function pathMatchesReservedPath(path: string, reservedPath: string): boolean {
  if (reservedPath === "/") {
    return path === "/";
  }

  return path === reservedPath || path.startsWith(`${reservedPath}/`);
}

function isRouteAuthRequirement(value: unknown): value is RouteAuthRequirement {
  if (!isRecord(value)) {
    return false;
  }

  if (value["kind"] === "public") {
    return value["permissions"] === undefined;
  }

  if (value["kind"] !== "authenticated") {
    return false;
  }

  const permissions = value["permissions"];
  return permissions === undefined || Array.isArray(permissions);
}

function isTenantRequirement(value: unknown): value is PlatformTenantRequirement {
  return value === "optional" || value === "required";
}

function isPlatformResourceAuthorization(value: unknown): value is PlatformResourceAuthorization {
  return isRecord(value) && typeof value["permission"] === "string" && typeof value["resolve"] === "function";
}

function isValidator(value: unknown): value is Validator<unknown> {
  return isRecord(value) && typeof value["validate"] === "function" && typeof value["explain"] === "function";
}

function isHandler(value: unknown): value is { readonly handle: (...args: readonly unknown[]) => unknown } {
  return isRecord(value) && typeof value["handle"] === "function";
}

function stringifyDetail(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  return String(value);
}

const permissionPattern = /^[^\s:]+:[^\s:]+$/;
const httpMethods: readonly HttpMethod[] = ["GET", "POST", "PUT", "PATCH", "DELETE"];
