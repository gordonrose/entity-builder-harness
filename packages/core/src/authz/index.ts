import type { Principal } from "../authn/index";
import { copyJsonValue, type JsonValue, type MessageDescriptor } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type Permission = `${string}:${string}`;
export type AuthorizationValue = JsonValue;
export type AuthorizationFacts = Readonly<Record<string, AuthorizationValue>>;
export type AuthorizationEvidence = Readonly<Record<string, AuthorizationValue>>;

export interface ResourceRef {
  readonly type: string;
  readonly id: string;
  readonly parent?: ResourceRef;
}

export interface AuthorizationRelation {
  readonly subject: ResourceRef;
  readonly relation: string;
  readonly object: ResourceRef;
}

export interface AuthorizationAttributes {
  readonly principal?: AuthorizationFacts;
  readonly tenant?: AuthorizationFacts;
  readonly resource?: AuthorizationFacts;
  readonly environment?: AuthorizationFacts;
}

export interface AuthorizationRequest {
  readonly principal: Principal;
  readonly permission: Permission;
  readonly tenantId?: TenantId;
  readonly resource?: ResourceRef;
  readonly relations?: readonly AuthorizationRelation[];
  readonly attributes?: AuthorizationAttributes;
  readonly facts?: AuthorizationFacts;
}

export type AuthorizationDecision =
  | {
      readonly allowed: true;
      readonly reason?: MessageDescriptor;
      readonly evidence?: AuthorizationEvidence;
    }
  | {
      readonly allowed: false;
      readonly reason: MessageDescriptor;
      readonly evidence?: AuthorizationEvidence;
    };

export interface Authorizer {
  decide(request: AuthorizationRequest): Promise<AuthorizationDecision>;
}

export function permission(resource: string, action: string): Permission {
  assertPermissionPart("resource", resource);
  assertPermissionPart("action", action);
  return `${resource}:${action}` as Permission;
}

export function resourceRef(input: {
  readonly type: string;
  readonly id: string;
  readonly parent?: ResourceRef;
}): ResourceRef {
  return {
    type: input.type,
    id: input.id,
    ...(input.parent === undefined ? {} : { parent: copyResourceRef(input.parent) }),
  };
}

export function authorizationRelation(input: {
  readonly subject: ResourceRef;
  readonly relation: string;
  readonly object: ResourceRef;
}): AuthorizationRelation {
  return {
    subject: copyResourceRef(input.subject),
    relation: input.relation,
    object: copyResourceRef(input.object),
  };
}

export function authorizationRequest(input: {
  readonly principal: Principal;
  readonly permission: Permission;
  readonly tenantId?: TenantId;
  readonly resource?: ResourceRef;
  readonly relations?: readonly AuthorizationRelation[];
  readonly attributes?: AuthorizationAttributes;
  readonly facts?: AuthorizationFacts;
}): AuthorizationRequest {
  return {
    principal: input.principal,
    permission: input.permission,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.resource === undefined ? {} : { resource: copyResourceRef(input.resource) }),
    ...(input.relations === undefined ? {} : { relations: input.relations.map(copyAuthorizationRelation) }),
    ...(input.attributes === undefined ? {} : { attributes: copyAuthorizationAttributes(input.attributes) }),
    ...(input.facts === undefined ? {} : { facts: copyAuthorizationFacts(input.facts) }),
  };
}

export function allow(input: {
  readonly reason?: MessageDescriptor;
  readonly evidence?: AuthorizationEvidence;
} = {}): AuthorizationDecision {
  return {
    allowed: true,
    ...(input.reason === undefined ? {} : { reason: input.reason }),
    ...(input.evidence === undefined ? {} : { evidence: copyAuthorizationFacts(input.evidence) }),
  };
}

export function deny(input: {
  readonly reason: MessageDescriptor;
  readonly evidence?: AuthorizationEvidence;
}): AuthorizationDecision {
  return {
    allowed: false,
    reason: input.reason,
    ...(input.evidence === undefined ? {} : { evidence: copyAuthorizationFacts(input.evidence) }),
  };
}

export function fixedAuthorizer(decision: AuthorizationDecision): Authorizer {
  return {
    decide: async () => decision,
  };
}

function copyResourceRef(resource: ResourceRef): ResourceRef {
  return {
    type: resource.type,
    id: resource.id,
    ...(resource.parent === undefined ? {} : { parent: copyResourceRef(resource.parent) }),
  };
}

function copyAuthorizationRelation(relation: AuthorizationRelation): AuthorizationRelation {
  return {
    subject: copyResourceRef(relation.subject),
    relation: relation.relation,
    object: copyResourceRef(relation.object),
  };
}

function copyAuthorizationAttributes(attributes: AuthorizationAttributes): AuthorizationAttributes {
  return {
    ...(attributes.principal === undefined ? {} : { principal: copyAuthorizationFacts(attributes.principal) }),
    ...(attributes.tenant === undefined ? {} : { tenant: copyAuthorizationFacts(attributes.tenant) }),
    ...(attributes.resource === undefined ? {} : { resource: copyAuthorizationFacts(attributes.resource) }),
    ...(attributes.environment === undefined ? {} : { environment: copyAuthorizationFacts(attributes.environment) }),
  };
}

function assertPermissionPart(name: "resource" | "action", value: string): void {
  if (value.length === 0 || value.trim() !== value || value.includes(":") || /\s/.test(value)) {
    throw new TypeError(`Permission ${name} must be a non-empty string without whitespace or colon separators.`);
  }
}

function copyAuthorizationFacts<TFacts extends AuthorizationFacts | AuthorizationEvidence>(facts: TFacts): TFacts {
  return Object.fromEntries(
    Object.entries(facts).map(([key, value]) => [key, copyAuthorizationValue(value)]),
  ) as TFacts;
}

function copyAuthorizationValue(value: AuthorizationValue): AuthorizationValue {
  return copyJsonValue(value, "authorization facts");
}
