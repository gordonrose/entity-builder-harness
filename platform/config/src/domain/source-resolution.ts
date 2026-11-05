import type { ConfigSettingRequirement, ConfigSource } from "@kanbien/core/config";
import { rejectPlatformConfigurationDeclaration } from "../contract/errors";

export function resolvePlatformConfigurationSource(requirements: readonly ConfigSettingRequirement[], bindings: Readonly<Record<string, string>>, source: ConfigSource): ConfigSource {
  if (!Array.isArray(requirements)) rejectPlatformConfigurationDeclaration("requirements", "wrong-type");
  if (typeof bindings !== "object" || bindings === null || Array.isArray(bindings)) rejectPlatformConfigurationDeclaration("bindings", "wrong-type");
  if (typeof source !== "object" || source === null || typeof source.get !== "function") rejectPlatformConfigurationDeclaration("source", "wrong-type");
  if (requirements.some(item => typeof item !== "object" || item === null || typeof item.setting !== "string")) rejectPlatformConfigurationDeclaration("requirements", "wrong-type");
  const names = requirements.map(item => item.setting);
  const keys = Reflect.ownKeys(bindings);
  if (keys.length !== names.length || keys.some(key => typeof key !== "string" || !names.includes(key))) rejectPlatformConfigurationDeclaration("bindings", "identity-count-mismatch");
  const snapshot: Record<string, string> = Object.create(null) as Record<string, string>;
  for (const name of names) {
    const field = Object.getOwnPropertyDescriptor(bindings, name);
    if (!field || !("value" in field)) rejectPlatformConfigurationDeclaration("bindings", "missing");
    const value: unknown = field.value;
    if (typeof value !== "string" || !/^[A-Za-z][A-Za-z0-9_.-]{0,127}$/.test(value)) rejectPlatformConfigurationDeclaration("bindings", "invalid-format");
    if (["constructor", "prototype", "__proto__"].includes(value)) rejectPlatformConfigurationDeclaration("bindings", "reserved");
    snapshot[name] = value;
  }
  return { get: setting => source.get(snapshot[setting]!) };
}
