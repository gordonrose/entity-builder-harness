import type { Brand, Result } from "../../shared/index";
import type { ConfigError } from "./reporting/errors";

export type EnvironmentName = Brand<string, "EnvironmentName">;

export type SecretReference = Brand<string, "SecretReference">;

export type ConfigValue = string | number | boolean | null;

export type ConfigRecord = Readonly<Record<string, ConfigValue | undefined>>;

export interface ConfigSource {
  get(key: string): ConfigValue | undefined;
}

export interface ConfigSchema<TConfig> {
  parse(source: ConfigSource): Result<TConfig, ConfigError>;
}


export type ConfigSettingRule = { readonly kind: "text"; readonly pattern?: RegExp }
  | { readonly kind: "integer"; readonly minimum: number; readonly maximum: number }
  | { readonly kind: "choice"; readonly values: readonly string[] };
export interface ConfigSettingRequirement { readonly setting: string; readonly rule: ConfigSettingRule }
export interface ConfigSettingDefinition extends ConfigSettingRequirement { readonly source: string }
export interface ConfigSettingRelationship<TSetting extends string = string> {
  readonly relationship: string;
  readonly rule: "must-differ";
  readonly left: TSetting;
  readonly right: TSetting;
}
