import type { Result } from "../shared/index";
import type { ValidationIssue } from "../validation/index";

export type ConfigValue = string | number | boolean | null;

export interface ConfigSource {
  get(key: string): ConfigValue | undefined;
}

export interface ConfigSchema<TConfig> {
  parse(source: ConfigSource): Result<TConfig, ConfigError>;
}

export interface ConfigError {
  readonly code: "CONFIG_INVALID" | "CONFIG_MISSING";
  readonly issues: readonly ValidationIssue[];
}
