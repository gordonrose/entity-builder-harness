import type { Principal } from "../authn/index";
import type { MessageDescriptor } from "../shared/index";

export type Permission = `${string}:${string}`;

export interface AuthorizationRequest {
  readonly principal: Principal;
  readonly permission: Permission;
  readonly resource?: string;
  readonly facts?: Readonly<Record<string, unknown>>;
}

export interface AuthorizationDecision {
  readonly allowed: boolean;
  readonly reason?: MessageDescriptor;
}

export interface Authorizer {
  decide(request: AuthorizationRequest): Promise<AuthorizationDecision>;
}
