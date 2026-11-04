import type { ConfigSettingRequirement, ConfigSettingRelationship, ConfigSource, ConfigSettingsFailure, ConfigSettingsRelationshipFailure } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";

export interface PlatformConfigurationLoadingInput<TConfig, TError> {
  readonly requirements: readonly ConfigSettingRequirement[];
  readonly bindings: Readonly<Record<string, string>>;
  readonly source: ConfigSource;
  readonly relationships?: readonly ConfigSettingRelationship[];
  readonly assemble: (values: Readonly<Record<string, string | number>>) => Result<TConfig, TError>;
}
export type PlatformConfigurationLoadingResult<TConfig, TError> = Result<TConfig, TError | ConfigSettingsFailure | ConfigSettingsRelationshipFailure>;
