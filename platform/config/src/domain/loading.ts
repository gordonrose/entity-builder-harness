import { validateConfigRequirements } from "@kanbien/core/config";
import type { PlatformConfigurationLoadingInput, PlatformConfigurationLoadingResult } from "../contract/loading";
import { rejectPlatformConfigurationDeclaration } from "../contract/errors";
import { resolvePlatformConfigurationSource } from "./source-resolution";

export function loadPlatformConfiguration<TConfig, TError = never>(input: PlatformConfigurationLoadingInput<TConfig, TError>): PlatformConfigurationLoadingResult<TConfig, TError> {
  if (typeof input.assemble !== "function") rejectPlatformConfigurationDeclaration("assembly", "wrong-type");
  const source = resolvePlatformConfigurationSource(input.requirements, input.bindings, input.source);
  const checked = input.relationships === undefined
    ? validateConfigRequirements(source, input.requirements)
    : validateConfigRequirements(source, input.requirements, input.relationships);
  return checked.ok ? input.assemble(checked.value) : checked;
}
