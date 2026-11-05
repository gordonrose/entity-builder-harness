import type { ConfigSettingsFailure, ConfigSettingRequirement, ConfigSource, Result } from "@kanbien/core";

export interface SqsSenderConfiguration { readonly queueUrl: string; readonly region: string }
export interface SqsWorkerConfiguration extends SqsSenderConfiguration {
  readonly waitTimeSeconds: number;
  readonly visibilityTimeoutSeconds: number;
}
export type SqsConfigurationCheck = (source: ConfigSource, requirements: readonly ConfigSettingRequirement[]) => Result<Readonly<Record<string, string | number>>, ConfigSettingsFailure>;
