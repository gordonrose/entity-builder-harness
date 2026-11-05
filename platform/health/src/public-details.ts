import type { HealthStatus } from "@kanbien/core/monitoring";

// Public health detail is an explicit disclosure contract, not a redactor.
// Do not add provider text, names, addresses or arbitrary scalar passthrough.
const summaries = Object.freeze({
  healthy: "Health check passed.",
  degraded: "Health check is degraded.",
  unhealthy: "Health check failed.",
} as const satisfies Readonly<Record<HealthStatus, string>>);
const metadataValues = Object.freeze({
  dependency: Object.freeze(["ready", "not-ready", "unknown"] as const),
  config: Object.freeze(["missing", "present"] as const),
});

export type PlatformPublicHealthMessage = (typeof summaries)[HealthStatus];
export interface PlatformPublicHealthMetadata {
  readonly dependency?: (typeof metadataValues.dependency)[number];
  readonly config?: (typeof metadataValues.config)[number];
  readonly failure?: "check-failed";
}

export function publicHealthMessage(status: HealthStatus): PlatformPublicHealthMessage {
  return summaries[status];
}

export function publicHealthMetadata(value: unknown): PlatformPublicHealthMetadata {
  const dependency = approvedMetadataValue(value, "dependency", metadataValues.dependency);
  const config = approvedMetadataValue(value, "config", metadataValues.config);
  return { ...(dependency === undefined ? {} : { dependency }), ...(config === undefined ? {} : { config }) };
}

function approvedMetadataValue<T extends string>(value: unknown, key: string, allowed: readonly T[]): T | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  try {
    const field = Object.getOwnPropertyDescriptor(value, key);
    return field && "value" in field && typeof field.value === "string" && allowed.includes(field.value as T) ? field.value as T : undefined;
  } catch { return undefined; /* Uninspectable optional detail is not public evidence. */ }
}
