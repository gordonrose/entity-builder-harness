import { withPlatformContractDiagnostic, type PlatformContractDiagnosticField, type PlatformContractDiagnosticCondition, type PlatformContractObserver } from "./registration-diagnostics";
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
import { isPlatformObservabilityRequirement } from "./observability-profiles";
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
  let field: PlatformContractDiagnosticField = "declaration";
  let condition: PlatformContractDiagnosticCondition = "object-required";
  const select = (location: PlatformContractDiagnosticField, fallback: PlatformContractDiagnosticCondition): void => {
    field = location; condition = fallback;
  };
  const failure = (error: PlatformContractError): Result<void, PlatformContractError> => contractFailure(withPlatformContractDiagnostic(error, "permission", field, condition));
  if (!isRecord(declaration)) {
    return failure(malformedPlatformPermission("Permission declaration must be an object."));
  }

  const declaredPermission = declaration["permission"];
  if (!(select("permission", typeof declaredPermission === "string" ? "invalid-format" : "string-required"), isPermission(declaredPermission))) {
    return failure(
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
  let field: PlatformContractDiagnosticField = "declaration";
  let condition: PlatformContractDiagnosticCondition = "object-required";
  const observe: PlatformContractObserver = (value) => { field = value.field; condition = value.condition; };
  const select = (location: PlatformContractDiagnosticField, fallback: PlatformContractDiagnosticCondition): void => {
    field = location; condition = fallback;
  };
  const failure = (error: PlatformContractError): Result<void, PlatformContractError> => contractFailure(withPlatformContractDiagnostic(error, "route", field, condition));
  if (!isRecord(route)) {
    return failure(malformedPlatformRoute("Route registration must be an object."));
  }

  const routeName = route["name"];
  if (!(select("name", typeof routeName === "string" ? "invalid-format" : "string-required"), isPlatformContractName(routeName))) {
    return failure(invalidContractName("platform route name", routeName));
  }

  const method = route["method"];
  if (!(select("method", typeof method === "string" ? "unsupported" : "string-required"), isHttpMethod(method))) {
    return failure(malformedPlatformRoute("Route method must be a supported HTTP method.", { method: stringifyDetail(method) }));
  }

  const path = route["path"];
  if (!(select("path", typeof path === "string" ? "invalid-format" : "string-required"), isRoutePath(path, observe))) {
    return failure(malformedPlatformRoute("Route path must be an absolute path without whitespace or URL scheme.", { path: stringifyDetail(path) }));
  }

  const reservedPath = findReservedPlatformRoutePath(path, options.reservedPaths ?? defaultReservedPlatformRoutePaths);
  if (reservedPath !== undefined) {
    field = "path"; condition = "reserved-path";
    return failure(reservedPlatformPath(path, reservedPath));
  }

  const auth = route["auth"];
  if (!(select("auth", "declaration-rejected"), isRouteAuthRequirement(auth, observe))) {
    return failure(malformedPlatformRoute("Route auth requirement must be public or authenticated."));
  }

  if (!(select("observability", "declaration-rejected"), isPlatformObservabilityRequirement(route["observability"], observe))) {
    return failure(malformedPlatformRoute("Route observability must reference a profile or provide a bounded justified opt-out."));
  }

  const tenantRequirement = route["tenant"];
  if (tenantRequirement !== undefined && !(select("tenant", "unsupported"), isTenantRequirement(tenantRequirement))) {
    return failure(malformedPlatformRoute("Route tenant requirement must be optional or required."));
  }

  const resourceAuthorization = route["resourceAuthorization"];
  if (resourceAuthorization !== undefined && !(select("resourceAuthorization", "declaration-rejected"), isPlatformResourceAuthorization(resourceAuthorization, observe))) {
    return failure(malformedPlatformRoute("Route resource authorization must declare a permission and resolve function."));
  }

  if (auth.kind === "public" && (tenantRequirement !== undefined || resourceAuthorization !== undefined)) {
    field = "auth"; condition = "public-controls";
    return failure(malformedPlatformRoute("Public routes cannot declare tenant or resource authorization controls."));
  }

  if (auth.kind === "authenticated") {
    const routePermissions = auth.permissions ?? [];
    for (const routePermission of routePermissions) {
      if (!(select("permission", typeof routePermission === "string" ? "invalid-format" : "string-required"), isPermission(routePermission))) {
        return failure(
          malformedPlatformRoute("Route permissions must use core resource:action permission strings.", {
            permission: stringifyDetail(routePermission),
          }),
        );
      }

      if (options.declaredPermissions !== undefined && !options.declaredPermissions.includes(routePermission)) {
        field = "permission"; condition = "undeclared-permission";
        return failure(unknownPlatformPermission(routePermission, options.declaredPermissions));
      }
    }

    if (resourceAuthorization !== undefined) {
      if (!(select("resourceAuthorization.permission", "invalid-format"), isPermission(resourceAuthorization.permission, (value) => { condition = value; }))) {
        return failure(
          malformedPlatformRoute("Route resource authorization permission must use a core resource:action permission string.", {
            permission: stringifyDetail(resourceAuthorization.permission),
          }),
        );
      }

      if (options.declaredPermissions !== undefined && !options.declaredPermissions.includes(resourceAuthorization.permission)) {
        field = "resourceAuthorization.permission"; condition = "undeclared-permission";
        return failure(unknownPlatformPermission(resourceAuthorization.permission, options.declaredPermissions));
      }
    }
  }

  const validator = route["validator"];
  if (validator !== undefined && !(select("validator", "declaration-rejected"), isValidator(validator, observe))) {
    return failure(malformedPlatformRoute("Route validator must implement the core Validator contract."));
  }

  if (!(select("handler", "declaration-rejected"), isHandler(route["handler"], observe))) {
    return failure(malformedPlatformRoute("Route handler must expose a handle function."));
  }

  return contractSuccess();
}

export function validatePlatformJobRegistration(job: PlatformJobRegistration): Result<void, PlatformContractError> {
  let field: PlatformContractDiagnosticField = "declaration";
  let condition: PlatformContractDiagnosticCondition = "object-required";
  const observe: PlatformContractObserver = (value) => { field = value.field; condition = value.condition; };
  const select = (location: PlatformContractDiagnosticField, fallback: PlatformContractDiagnosticCondition): void => {
    field = location; condition = fallback;
  };
  const failure = (error: PlatformContractError): Result<void, PlatformContractError> => contractFailure(withPlatformContractDiagnostic(error, "job", field, condition));
  if (!isRecord(job)) {
    return failure(malformedPlatformJob("Job registration must be an object."));
  }

  const jobName = job["name"];
  if (!(select("name", typeof jobName === "string" ? "invalid-format" : "string-required"), isPlatformContractName(jobName))) {
    return failure(invalidContractName("platform job name", jobName));
  }

  const messageType = job["messageType"];
  if (!(select("messageType", typeof messageType === "string" ? "invalid-format" : "string-required"), isPlatformContractName(messageType))) {
    return failure(
      malformedPlatformJob("Job message type must use dot-separated lowercase segments.", {
        messageType: stringifyDetail(messageType),
      }),
    );
  }

  if (!(select("observability", "declaration-rejected"), isPlatformObservabilityRequirement(job["observability"], observe))) {
    return failure(malformedPlatformJob("Job observability must reference a profile or provide a bounded justified opt-out."));
  }

  const validator = job["validator"];
  if (validator !== undefined && !(select("validator", "declaration-rejected"), isValidator(validator, observe))) {
    return failure(malformedPlatformJob("Job validator must implement the core Validator contract."));
  }

  if (!(select("handler", "declaration-rejected"), isHandler(job["handler"], observe))) {
    return failure(malformedPlatformJob("Job handler must expose a handle function."));
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

function isPermission(value: unknown, observe?: (condition: "string-required" | "invalid-format") => void): value is Permission {
  if (typeof value !== "string") { observe?.("string-required"); return false; }
  if (!permissionPattern.test(value)) { observe?.("invalid-format"); return false; }
  return true;
}

function isHttpMethod(value: unknown): value is HttpMethod {
  return typeof value === "string" && httpMethods.includes(value as HttpMethod);
}

function isRoutePath(value: unknown, observer?: PlatformContractObserver): value is string {
  if (typeof value !== "string") return rejected(observer, "path", "string-required");
  if (!value.startsWith("/")) return rejected(observer, "path", "path-not-absolute");
  if (/\s/.test(value)) return rejected(observer, "path", "path-whitespace");
  return !value.includes("://") || rejected(observer, "path", "path-url-scheme");
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

function rejected(observer: PlatformContractObserver | undefined, field: PlatformContractDiagnosticField, condition: PlatformContractDiagnosticCondition): false {
  observer?.({ field, condition }); return false;
}
function isRouteAuthRequirement(value: unknown, observer?: PlatformContractObserver): value is RouteAuthRequirement {
  if (!isRecord(value)) return rejected(observer, "auth", "object-required");
  if (value["kind"] === "public") return value["permissions"] === undefined || rejected(observer, "auth.permissions", "public-permissions");
  if (value["kind"] !== "authenticated") return rejected(observer, "auth.kind", "unsupported");
  const permissions = value["permissions"];
  return permissions === undefined || Array.isArray(permissions) || rejected(observer, "auth.permissions", "permissions-array-required");
}
function isTenantRequirement(value: unknown): value is PlatformTenantRequirement {
  return value === "optional" || value === "required";
}
function isPlatformResourceAuthorization(value: unknown, observer?: PlatformContractObserver): value is PlatformResourceAuthorization {
  if (!isRecord(value)) return rejected(observer, "resourceAuthorization", "object-required");
  if (typeof value["permission"] !== "string") return rejected(observer, "resourceAuthorization.permission", "string-required");
  if (typeof value["resolve"] !== "function") return rejected(observer, "resourceAuthorization.resolve", "function-required");
  return true;
}
function isValidator(value: unknown, observer?: PlatformContractObserver): value is Validator<unknown> {
  if (!isRecord(value)) return rejected(observer, "validator", "object-required");
  if (typeof value["validate"] !== "function") return rejected(observer, "validator.validate", "function-required");
  if (typeof value["explain"] !== "function") return rejected(observer, "validator.explain", "function-required");
  return true;
}
function isHandler(value: unknown, observer?: PlatformContractObserver): value is { readonly handle: (...args: readonly unknown[]) => unknown } {
  if (!isRecord(value)) return rejected(observer, "handler", "object-required");
  if (typeof value["handle"] !== "function") return rejected(observer, "handler.handle", "function-required");
  return true;
}

function stringifyDetail(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  return String(value);
}

const permissionPattern = /^[^\s:]+:[^\s:]+$/;
const httpMethods: readonly HttpMethod[] = ["GET", "POST", "PUT", "PATCH", "DELETE"];
