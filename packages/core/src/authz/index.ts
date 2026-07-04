import type { Principal } from "../authn/index";

export type Permission = `${string}:${string}`;

export interface AuthorizationRequest {
  readonly principal: Principal;
  readonly permission: Permission;
  readonly resource?: string;
  readonly facts?: Readonly<Record<string, unknown>>;
}

export interface AuthorizationDecision {
  readonly allowed: boolean;
  readonly reason?: string;
}

export interface Authorizer {
  decide(request: AuthorizationRequest): Promise<AuthorizationDecision>;
}
