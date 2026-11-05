import type { Principal } from "@kanbien/core/authn";
import type { Brand, CorrelationId, JsonValue, Result } from "@kanbien/core/shared";
import type { TenantContext } from "@kanbien/core/tenancy";
import type { PlatformContractError } from "./errors";
import { brandedPlatformContractName } from "./identifiers";
import { PlatformOperationalObservation, type PlatformOperationalDiagnosticOptions } from "./operational-observations";

export type FeatureFlagName = Brand<string, "FeatureFlagName">;

export interface FeatureFlagContext {
  readonly tenant?: TenantContext;
  readonly principal?: Principal;
  readonly correlationId?: CorrelationId;
  readonly facts?: Readonly<Record<string, JsonValue>>;
}

export interface FeatureFlagReader {
  isEnabled(name: FeatureFlagName, context?: FeatureFlagContext): Promise<boolean> | boolean;
}

export function featureFlagName(value: string): Result<FeatureFlagName, PlatformContractError> {
  return brandedPlatformContractName(value, "FeatureFlagName", "feature flag name");
}

export function fixedFeatureFlagReader(flags: Readonly<Record<string, boolean>>, defaultEnabled = false, diagnostics?: PlatformOperationalDiagnosticOptions): FeatureFlagReader {
  const snapshotObservation = new PlatformOperationalObservation("fixed-feature-flags", "reader-not-produced", diagnostics);
  const snapshot = snapshotObservation.run(() => ({ ...flags }));

  return {
    isEnabled: (name) => {
      const observation = new PlatformOperationalObservation("fixed-feature-flags", "value-not-produced", diagnostics);
      observation.location("read", "value");
      return observation.run(() => snapshot[name] ?? defaultEnabled);
    },
  };
}
