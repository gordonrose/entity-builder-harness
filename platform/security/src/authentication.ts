import {
  principal,
  principalId,
  coreDiagnosticCatalog,
  type Permission,
  type Principal,
  type PrincipalClaims,
  type PrincipalType,
} from "@kanbien/core";
import {
  authzMappingPermissions,
  observePermissionsFromClaims,
  type PlatformAuthzPermissionMapping,
} from "./authorization";
import type { PlatformJwtVerifier } from "./jwt";
import { captureDiagnosticRecord, diagnosticProcessingRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { observeSecurityFailure, securityFailureDiagnosticRecord, securityDiagnosticRecordsFrom, securityOperationDiagnosticRecord, platformSecurityDiagnosticCatalog, securityPrincipalBoundaryDiagnosticRecord, type SecurityPrincipalBoundaryDetail } from "./diagnostics";

export interface PlatformAuthenticationResult {
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly authenticated: boolean;
  readonly permissions: readonly Permission[];
  readonly principalId?: string;
  readonly principalType?: PrincipalType;
  readonly subject?: string;
  readonly claims?: PrincipalClaims;
  readonly scopes?: readonly string[];
  readonly rateLimitKey?: string;
}

export interface PlatformAuthenticationRequest {
  readonly headers?: Readonly<Record<string, string | readonly string[]>>;
}

export interface PlatformAuthenticationHook {
  authenticate(request: PlatformAuthenticationRequest): Promise<PlatformAuthenticationResult> | PlatformAuthenticationResult;
  grantedPermissions?(): readonly Permission[];
}

export interface JwtBearerAuthenticationHookOptions {
  readonly verifier: PlatformJwtVerifier;
  readonly authz: PlatformAuthzPermissionMapping;
  readonly principalType?: PrincipalType;
}

export const denyByDefaultAuthenticationResult: PlatformAuthenticationResult = {
  authenticated: false,
  permissions: [],
};

export type PlatformPrincipalMissingAttribute = "principal-id" | "principal-type" | "subject";
export interface PlatformPrincipalDiagnosticContext {
  readonly operation: "principal-from-authentication";
  readonly evidence: "owned" | "source";
}
export interface PlatformPrincipalDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: PlatformPrincipalDiagnosticContext) => unknown;
  readonly onMissingAttribute?: (attribute: PlatformPrincipalMissingAttribute) => unknown;
}
const principalNativeThen = Promise.prototype.then;
function isolatePrincipalObservation(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(principalNativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(principalNativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional sink. */ } }
}

export function principalFromPlatformAuthenticationResult(
  authentication: PlatformAuthenticationResult,
  diagnostics?: PlatformPrincipalDiagnosticOptions,
): Principal | undefined {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformSecurityDiagnosticCatalog.definitions];
  let selectionFailed = false;
  try { definitions = [...definitions, ...(diagnostics?.diagnosticDefinitions ?? [])]; } catch { selectionFailed = true; }
  const deliver = (record: DiagnosticRecord, evidence: PlatformPrincipalDiagnosticContext["evidence"]): void => {
    const checked = requireDiagnosticRecord(definitions, record);
    try { isolatePrincipalObservation(diagnostics?.onDiagnostic?.(checked, Object.freeze({ operation: "principal-from-authentication", evidence }))); } catch { /* Keep raw result/throw. */ }
    if (selectionFailed) {
      selectionFailed = false;
      deliver(diagnosticProcessingRecord("definition-selection-failed"), "owned");
    }
  };
  const observe = (build: () => DiagnosticRecord, cause?: unknown): void => {
    deliver(captureDiagnosticRecord(build), "owned");
    const selected = selectDiagnosticEvidenceWithReport(definitions, cause, (record) => deliver(record, "source"));
    if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord, "source");
    for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record, "source");
  };
  let field: SecurityPrincipalBoundaryDetail["field"] = "authenticated";
  const read = <T>(attribute: SecurityPrincipalBoundaryDetail["field"], action: () => T): T => { field = attribute; return action(); };
  const missing = (attribute: PlatformPrincipalMissingAttribute, absent: boolean): boolean => {
    if (absent) {
      try { isolatePrincipalObservation(diagnostics?.onMissingAttribute?.(attribute)); } catch { /* Optional guard observer. */ }
      observe(() => securityOperationDiagnosticRecord("authentication", "principal-attribute-missing", { attribute }));
    }
    return absent;
  };
  let constructing = false;
  try {
    if (
      !read("authenticated", () => authentication.authenticated)
      || missing("principal-id", read("principal-id", () => authentication.principalId) === undefined)
      || missing("principal-type", read("principal-type", () => authentication.principalType) === undefined)
      || missing("subject", read("subject", () => authentication.subject) === undefined)
    ) return undefined;

    return principal({
      id: principalId(read("principal-id", () => authentication.principalId)!),
      type: read("principal-type", () => authentication.principalType)!,
      subject: read("subject", () => authentication.subject)!,
      claims: read("claims", () => authentication.claims) ?? {},
      scopes: read("scopes", () => authentication.scopes) ?? [],
    }, (constructing = true, { diagnosticDefinitions: definitions, onDiagnostic(record, context) { deliver(record, context.evidence); } }));
  } catch (cause) {
    // The Core constructor owns its copy/iteration failures and reports them
    // directly through the bridge; do not invent a second projection failure.
    if (!constructing) observe(() => securityPrincipalBoundaryDiagnosticRecord(field), cause);
    throw cause;
  }
}

export function createJwtBearerAuthenticationHook(
  options: JwtBearerAuthenticationHookOptions,
): PlatformAuthenticationHook {
  const granted = authzMappingPermissions(options.authz);

  return {
    grantedPermissions: () => granted,
    async authenticate(request) {
      const bearer = observeBearerTokenFromHeaders(request.headers ?? {});
      if (bearer.token === undefined) {
        return { ...denyByDefaultAuthenticationResult, diagnosticRecord: bearer.diagnosticRecord! };
      }

      let verified: Awaited<ReturnType<PlatformJwtVerifier["verify"]>>;
      try { verified = await options.verifier.verify(bearer.token); }
      catch (error) { throw observeSecurityFailure(error, securityFailureDiagnosticRecord(error) ?? securityOperationDiagnosticRecord("authentication", "verifier-failed"), securityDiagnosticRecordsFrom(error).slice(1)); }
      if (!verified.ok) {
        const related = securityDiagnosticRecordsFrom(verified.error).slice(1);
        return { ...denyByDefaultAuthenticationResult, diagnosticRecord: securityFailureDiagnosticRecord(verified.error) ?? securityOperationDiagnosticRecord("authentication", "verifier-rejected-unclassified"), ...(related.length === 0 ? {} : { relatedDiagnosticRecords: related }) };
      }

      const subject = stringClaim(verified.value.claims, "sub");
      if (subject === undefined) {
        const raw = verified.value.claims["sub"];
        return { ...denyByDefaultAuthenticationResult, diagnosticRecord: securityOperationDiagnosticRecord("authentication", raw === undefined ? "subject-missing" : typeof raw !== "string" ? "subject-wrong-type" : "subject-empty") };
      }

      const scopes = scopesFromClaims(verified.value.claims);
      const mapped = observePermissionsFromClaims(verified.value.claims, options.authz);
      const observations = [...securityDiagnosticRecordsFrom(verified.value), ...mapped.relatedDiagnosticRecords];
      const concrete = observations.filter((record) => !record.code.endsWith(".additional-observations-omitted"));
      const previouslyOmitted = observations.filter((record) => record.code.endsWith(".additional-observations-omitted")).reduce((count, record) => Math.min(Number.MAX_SAFE_INTEGER, count + (record.detail as { omittedCount: number }).omittedCount), 0);
      const relatedDiagnosticRecords = concrete.length <= 8 && previouslyOmitted === 0 ? concrete : [...concrete.slice(0, 7), securityOperationDiagnosticRecord("authentication", "additional-observations-omitted", { omittedCount: Math.min(Number.MAX_SAFE_INTEGER, previouslyOmitted + Math.max(0, concrete.length - 7)) })];
      return {
        authenticated: true,
        permissions: mapped.permissions,
        ...(relatedDiagnosticRecords.length === 0 ? {} : { relatedDiagnosticRecords }),
        principalId: principalId(subject),
        principalType: options.principalType ?? "user",
        subject,
        claims: verified.value.claims,
        scopes,
        rateLimitKey: `principal:${subject}`,
      };
    },
  };
}

export function bearerTokenFromHeaders(headers: Readonly<Record<string, string | readonly string[]>>): string | undefined {
  return observeBearerTokenFromHeaders(headers).token;
}

export function observeBearerTokenFromHeaders(headers: Readonly<Record<string, string | readonly string[]>>): { readonly token?: string; readonly diagnosticRecord?: DiagnosticRecord } {
  const authorization = firstHeaderValue(headers, "authorization");
  if (authorization === undefined) {
    return { diagnosticRecord: securityOperationDiagnosticRecord("authentication-header", "missing") };
  }

  const match = /^Bearer\s+(.+)$/i.exec(authorization);
  return match?.[1] === undefined ? { diagnosticRecord: securityOperationDiagnosticRecord("authentication-header", /^Bearer(?:\s|$)/i.test(authorization) || authorization.length === 0 ? "malformed-bearer" : "unsupported-scheme") } : { token: match[1] };
}

export function firstHeaderValue(headers: Readonly<Record<string, string | readonly string[]>>, name: string): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name.toLowerCase());
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}

function scopesFromClaims(claims: PrincipalClaims): readonly string[] {
  const scope = stringClaim(claims, "scope");
  if (scope === undefined) {
    return [];
  }

  return scope.split(/\s+/).filter((item) => item.length > 0);
}

function stringClaim(claims: PrincipalClaims, name: string): string | undefined {
  const value = claims[name];
  return typeof value === "string" && value.length > 0 ? value : undefined;
}
