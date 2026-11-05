import { createConfigIssueCollector, stringConfigValue, numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import type { PlatformJwtVerificationOptions, PlatformJwtClaimRequirement, PlatformJwtClaimScalar } from "../../jwt-contract";
import { jwtDefaultClockSkewSeconds, type CheckedJwtVerifierConfiguration, type JwtConfigurationSetting, type JwtConfigurationReason } from "../contract/requirements";
import { jwtConfigurationDiagnosticRecord } from "../contract/reporting/diagnostics";
import type { JwtConfigurationFailure } from "../contract/reporting/errors";

export function validateJwtVerifierConfiguration(options: PlatformJwtVerificationOptions): Result<CheckedJwtVerifierConfiguration, JwtConfigurationFailure> {
  const collected = createConfigIssueCollector<JwtConfigurationReason>();
  const add = (setting: JwtConfigurationSetting, reason: JwtConfigurationReason, index?: number, attributeIndex?: number): void => {
    collected.add({ setting, reason, ...(index === undefined ? {} : { index }), ...(attributeIndex === undefined ? {} : { attributeIndex }) });
  };
  const text = (setting: JwtConfigurationSetting, value: unknown, index?: number): boolean => {
    const checked = stringConfigValue({ get: () => value } as ConfigSource, setting);
    const reason = !checked.ok ? value === undefined ? "missing" : "wrong-type" : checked.value.length === 0 ? "empty"
      : checked.value.trim().length === 0 ? "blank" : checked.value.trim() !== checked.value ? "surrounding-whitespace" : undefined;
    if (reason !== undefined) add(setting, reason, index);
    return reason === undefined;
  };
  let issuer: unknown, jwksUri: unknown, skew: unknown, required: unknown, clock: PlatformJwtVerificationOptions["clock"], fetcher: PlatformJwtVerificationOptions["fetchJwks"];
  if (typeof options !== "object" || options === null || Array.isArray(options)) {
    add("configuration", "wrong-type");
    return { ok: false, error: { code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID", diagnosticRecord: jwtConfigurationDiagnosticRecord(collected.finish()) } };
  }
  else { issuer = options.issuer; jwksUri = options.jwksUri; skew = options.clockSkewSeconds; required = options.requiredClaims; clock = options.clock; fetcher = options.fetchJwks; }
  text("issuer", issuer);
  const sourceTextValid = text("key-source", jwksUri);
  if (sourceTextValid && fetcher === undefined) {
    try { const parsed = new URL(jwksUri as string); if (parsed.protocol !== "https:") add("key-source", "unsupported-scheme"); }
    catch { add("key-source", "invalid-format"); }
  }
  const tolerance = skew === undefined ? jwtDefaultClockSkewSeconds : skew;
  const number = numberConfigValue({ get: () => tolerance } as ConfigSource, "clock-tolerance");
  if (!number.ok) add("clock-tolerance", typeof tolerance === "number" ? "not-finite" : "wrong-type");
  else if (number.value < 0) add("clock-tolerance", "negative");
  const rules: PlatformJwtClaimRequirement[] = [];
  const scalar = (value: unknown): value is PlatformJwtClaimScalar => typeof value === "string" || typeof value === "boolean" || typeof value === "number" && Number.isFinite(value);
  if (required !== undefined && !Array.isArray(required)) add("required-claims", "wrong-type");
  else if (Array.isArray(required)) for (let index = 0; index < required.length; index++) {
    const entry: unknown = required[index];
    if (typeof entry !== "object" || entry === null || Array.isArray(entry)) { add("required-claims", "wrong-type", index); continue; }
    const rule = entry as Record<string, unknown>, claim = rule["claim"];
    text("required-claim.name", claim, index);
    const exact = "equals" in rule, oneOf = "oneOf" in rule;
    if (exact === oneOf) { add("required-claim.comparison", exact ? "comparison-conflict" : "comparison-missing", index); continue; }
    if (exact) {
      const value = rule["equals"];
      if (!scalar(value)) add("required-claim.value", "unsupported-value", index);
      else rules.push(Object.freeze({ claim: claim as string, equals: value }));
    } else {
      const values = rule["oneOf"];
      if (!Array.isArray(values)) { add("required-claim.value", "wrong-type", index); continue; }
      if (values.length === 0) add("required-claim.value", "empty", index);
      const accepted: PlatformJwtClaimScalar[] = [];
      for (let position = 0; position < values.length; position++) {
        const value: unknown = values[position];
        if (!scalar(value)) add("required-claim.value", "unsupported-value", index, position);
        else accepted.push(value);
      }
      rules.push(Object.freeze({ claim: claim as string, oneOf: Object.freeze(accepted) }));
    }
  }
  let selectedClock: PlatformJwtVerificationOptions["clock"], selectedFetcher: PlatformJwtVerificationOptions["fetchJwks"];
  if (clock !== undefined) {
    const now = clock !== null && (typeof clock === "object" || typeof clock === "function") ? clock.now : undefined;
    if (typeof now !== "function") add("clock.now", "not-callable");
    else selectedClock = Object.freeze({ now: () => Reflect.apply(now, clock, []) as Date });
  }
  if (fetcher !== undefined) {
    const fetch = fetcher !== null && (typeof fetcher === "object" || typeof fetcher === "function") ? fetcher.fetch : undefined;
    if (typeof fetch !== "function") add("key-fetcher.fetch", "not-callable");
    else selectedFetcher = Object.freeze({ fetch: (uri: string) => Reflect.apply(fetch, fetcher, [uri]) as ReturnType<typeof fetch> });
  }
  const issues = collected.finish();
  if (issues.issues.length !== 0) return { ok: false, error: { code: "PLATFORM_SECURITY_JWT_CONFIGURATION_INVALID", diagnosticRecord: jwtConfigurationDiagnosticRecord(issues) } };
  return { ok: true, value: Object.freeze({ issuer: issuer as string, jwksUri: jwksUri as string, clockSkewSeconds: tolerance as number,
    requiredClaims: Object.freeze(rules), ...(selectedClock === undefined ? {} : { clock: selectedClock }), ...(selectedFetcher === undefined ? {} : { fetchJwks: selectedFetcher }) }) };
}
