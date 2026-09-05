import type { Brand, Result } from "@kanbien/core/shared";
import { invalidContractName, type PlatformContractError } from "./errors";

export type PlatformAppId = Brand<string, "PlatformAppId">;
export type PlatformRouteName = Brand<string, "PlatformRouteName">;
export type PlatformJobName = Brand<string, "PlatformJobName">;
export type PlatformHealthName = Brand<string, "PlatformHealthName">;
export type PlatformApiVersion = Brand<string, "PlatformApiVersion">;

export function platformAppId(value: string): Result<PlatformAppId, PlatformContractError> {
  return brandedPlatformContractName(value, "PlatformAppId", "platform app id");
}

export function platformRouteName(value: string): Result<PlatformRouteName, PlatformContractError> {
  return brandedPlatformContractName(value, "PlatformRouteName", "platform route name");
}

export function platformJobName(value: string): Result<PlatformJobName, PlatformContractError> {
  return brandedPlatformContractName(value, "PlatformJobName", "platform job name");
}

export function platformHealthName(value: string): Result<PlatformHealthName, PlatformContractError> {
  return brandedPlatformContractName(value, "PlatformHealthName", "platform health name");
}

export function platformApiVersion(value: string): Result<PlatformApiVersion, PlatformContractError> {
  return brandedPlatformContractName(value, "PlatformApiVersion", "platform api version");
}

export function brandedPlatformContractName<TName extends string>(
  value: string,
  brandName: TName,
  label: string,
): Result<Brand<string, TName>, PlatformContractError> {
  if (!isPlatformContractName(value)) {
    return {
      ok: false,
      error: invalidContractName(label, value),
    };
  }

  return {
    ok: true,
    value: value as Brand<string, TName>,
  };
}

export function isPlatformContractName(value: unknown): value is string {
  return typeof value === "string" && contractNamePattern.test(value);
}

const contractNamePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;
