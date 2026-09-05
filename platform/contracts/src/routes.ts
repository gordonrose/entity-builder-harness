import type { Principal } from "@kanbien/core/authn";
import type {
  AuthorizationAttributes,
  AuthorizationFacts,
  AuthorizationRelation,
  Permission,
  ResourceRef,
} from "@kanbien/core/authz";
import type { TenantResolver } from "@kanbien/core/tenancy";
import type { Validator } from "@kanbien/core/validation";
import type { PlatformRequestContext } from "./contexts";
import type { PlatformApiVersion, PlatformRouteName } from "./identifiers";

export type HttpMethod = PlatformRequestContext["method"];

export type RouteAuthRequirement =
  | {
      readonly kind: "public";
    }
  | {
      readonly kind: "authenticated";
      readonly permissions?: readonly Permission[];
    };

export type PlatformTenantRequirement = "optional" | "required";

export type PlatformResourceNotFoundDisclosure = "not-found" | "forbidden";

export interface PlatformRequest<TBody = unknown> {
  readonly params: Readonly<Record<string, string>>;
  readonly query: Readonly<Record<string, string | readonly string[]>>;
  readonly headers: Readonly<Record<string, string | readonly string[]>>;
  readonly body?: TBody;
}

export interface PlatformResourceAuthorizationInput<TBody = unknown> {
  readonly request: PlatformRequest<TBody>;
  readonly context: PlatformRequestContext;
}

export type PlatformResourceAuthorizationResolution =
  | {
      readonly kind: "not-found";
      readonly disclosure: PlatformResourceNotFoundDisclosure;
    }
  | {
      readonly kind: "authorize";
      readonly resource?: ResourceRef;
      readonly relations?: readonly AuthorizationRelation[];
      readonly attributes?: AuthorizationAttributes;
      readonly facts?: AuthorizationFacts;
    };

export interface PlatformResourceAuthorization<TBody = unknown> {
  readonly permission: Permission;
  resolve(
    input: PlatformResourceAuthorizationInput<TBody>,
  ): Promise<PlatformResourceAuthorizationResolution> | PlatformResourceAuthorizationResolution;
}

export interface PlatformResponse<TBody = unknown> {
  readonly status: number;
  readonly body?: TBody;
  readonly headers?: Readonly<Record<string, string>>;
}

export interface PlatformRouteHandler<TBody = unknown, TResponse = unknown> {
  handle(
    request: PlatformRequest<TBody>,
    context: PlatformRequestContext,
  ): Promise<PlatformResponse<TResponse>> | PlatformResponse<TResponse>;
}

export interface PlatformRouteRegistration<TBody = unknown, TResponse = unknown> {
  readonly name: PlatformRouteName;
  readonly method: HttpMethod;
  readonly path: string;
  readonly apiVersion?: PlatformApiVersion;
  readonly auth: RouteAuthRequirement;
  readonly tenant?: PlatformTenantRequirement;
  readonly resourceAuthorization?: PlatformResourceAuthorization<TBody>;
  readonly validator?: Validator<TBody>;
  readonly handler: PlatformRouteHandler<TBody, TResponse>;
}

export interface PlatformTenantResolutionInput {
  readonly route: Pick<PlatformRouteRegistration, "name" | "method" | "path" | "apiVersion">;
  readonly request: PlatformRequest;
  readonly principal: Principal;
}

export type PlatformTenantResolver = TenantResolver<PlatformTenantResolutionInput>;
